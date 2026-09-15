import re
import logging
import json
import time
import uuid
import hashlib
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import Session
from .config import settings
from .access import protect
from .context import generation_history
from .editing import fit_essay
from .db import Artifact, Base, ChatSession, Chunk, Message, SessionLocal, Transcript, engine, get_db, now
from .retrieval import contextual_query, index
from .service import generate, route_mode, verify_citations, word_count, quotation_warnings, attribution_warnings, evidence_fallback

logger = logging.getLogger('lenny')
logging.basicConfig(level=logging.INFO, format='%(message)s')


@asynccontextmanager
async def lifespan(app):
    try:
        Base.metadata.create_all(engine)
    except SQLAlchemyError:
        logger.error(json.dumps({'event': 'startup_database_unavailable'}))
    yield


app = FastAPI(title='Lenny Growth Assistant', version='1.0.0', lifespan=lifespan)


app.middleware('http')(protect)


@app.middleware('http')
async def request_log(request: Request, call_next):
    rid = str(uuid.uuid4())
    request.state.request_id = rid
    start = time.monotonic()
    response = await call_next(request)
    response.headers['X-Request-ID'] = rid
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    if request.url.path.startswith('/api'):
        response.headers['Cache-Control'] = 'no-store'
    elif request.url.path.startswith('/assets/'):
        response.headers['Cache-Control'] = 'private, max-age=31536000, immutable'
    else:
        response.headers['Cache-Control'] = 'no-cache'
    logger.info(json.dumps({'event':'http_request', 'request_id':rid, 'method':request.method,
        'path':request.url.path, 'status':response.status_code, 'duration_ms':round((time.monotonic()-start)*1000)}))
    return response


def error_response(request, code, message, status):
    return JSONResponse(status_code=status, content={'error': {'code':code, 'message':message,
        'request_id':getattr(request.state, 'request_id', '')}})


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    detail = exc.detail if isinstance(exc.detail, dict) else {'code':'request_error','message':str(exc.detail)}
    return error_response(request, detail.get('code','request_error'), detail.get('message','Request failed'), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return error_response(request, 'invalid_request', 'Check the request fields. Message text must be 1–8,000 characters and identifiers must be valid UUIDs.', 422)


@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    logger.error(json.dumps({'event':'database_error', 'type':type(exc).__name__}))
    return error_response(request, 'database_unavailable', 'The database is unavailable. Check PostgreSQL and DATABASE_URL, then retry.', 503)


def owner_id(x_workspace_id: uuid.UUID = Header()):
    return str(x_workspace_id)


def owned(db, session_id, owner, lock=False):
    stmt = select(ChatSession).where(ChatSession.id == str(session_id), ChatSession.owner == owner)
    if lock:
        stmt = stmt.with_for_update(nowait=True)
    try:
        row = db.scalar(stmt)
    except DBAPIError as exc:
        if getattr(exc.orig, 'sqlstate', '') == '55P03':
            raise HTTPException(409, detail={'code':'session_busy', 'message':'A response is already being written in this conversation.'})
        raise
    if row is None:
        raise HTTPException(404, detail={'code':'not_found','message':'This conversation could not be found.'})
    return row


def artifact_out(a):
    return {'id':a.id, 'title':a.title, 'format':a.format, 'content':a.content,
        'sources':a.sources, 'created_at':a.created_at.isoformat()}


def message_out(m):
    details = dict(m.details or {})
    if m.role == 'assistant' and not details.get('artifact_id'):
        warnings = details.get('warnings', []) + attribution_warnings(m.content, details.get('sources', []))
        details['warnings'] = list(dict.fromkeys(warnings))
    return {'id':m.id, 'role':m.role, 'content':m.content, 'created_at':m.created_at.isoformat(), **details}


def session_out(s):
    return {'id':s.id, 'title':s.title, 'created_at':s.created_at.isoformat(), 'updated_at':s.updated_at.isoformat()}


class CreateSession(BaseModel):
    display_name: str = Field(default='Guest', max_length=60)
    timezone: str = Field(default='UTC', max_length=80)


class ChatInput(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    mode: Literal['auto','ask','essay','markdown','html'] = 'auto'
    provider: Literal['ollama','anthropic'] | None = None


@app.get('/api/health/live')
def live():
    return {'status':'ok', 'service':'lenny-growth-studio',
            'workspace':hashlib.sha256(str(Path.cwd().resolve()).encode()).hexdigest()[:16]}


@app.get('/api/health/ready')
def ready(db: Session = Depends(get_db)):
    db.execute(text('SELECT 1'))
    count = db.scalar(select(func.count()).select_from(Transcript))
    if not count:
        raise HTTPException(503, detail={'code':'knowledge_empty','message':'Import transcripts with python -m backend.ingest.'})
    return {'status':'ready', 'transcripts':count}


@app.get('/api/status')
def status(db: Session = Depends(get_db)):
    cfg = settings()
    count = db.scalar(select(func.count()).select_from(Transcript))
    chunk_count = db.scalar(select(func.count()).select_from(Chunk))
    ollama = False
    agent = False
    try:
        r = httpx.get(cfg.ollama_base_url + '/api/tags', timeout=2)
        ollama = r.is_success and any(m['name'] == cfg.ollama_model or m['name'] == cfg.ollama_model+':latest' for m in r.json().get('models', []))
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    try:
        agent = httpx.get(cfg.agent_url + '/health', timeout=2).is_success
    except httpx.HTTPError:
        pass
    return {'transcripts':count, 'chunks':chunk_count, 'database':True, 'agent':agent,
        'default_provider':cfg.llm_provider, 'providers':[
            {'id':'ollama', 'label':'Local · Ollama', 'model':cfg.ollama_model, 'available':ollama},
            {'id':'anthropic','label':'Cloud · Anthropic','model':cfg.anthropic_model,'available':bool(cfg.anthropic_api_key)}
        ]}


@app.get('/api/sessions')
def sessions(owner=Depends(owner_id), db: Session=Depends(get_db)):
    return [session_out(s) for s in db.scalars(select(ChatSession).where(ChatSession.owner==owner).order_by(ChatSession.updated_at.desc()).limit(100))]


@app.post('/api/sessions', status_code=201)
def create_session(body:CreateSession, owner=Depends(owner_id), db:Session=Depends(get_db)):
    row = ChatSession(owner=owner, user_metadata=body.model_dump())
    db.add(row)
    db.commit()
    return session_out(row)


@app.get('/api/sessions/{session_id}')
def get_session(session_id:uuid.UUID, owner=Depends(owner_id), db:Session=Depends(get_db)):
    row = owned(db, session_id, owner)
    messages = db.scalars(select(Message).where(Message.session_id==row.id).order_by(Message.created_at, Message.id)).all()
    artifacts = db.scalars(select(Artifact).where(Artifact.session_id==row.id).order_by(Artifact.created_at)).all()
    return {**session_out(row), 'messages':[message_out(m) for m in messages], 'artifacts':[artifact_out(a) for a in artifacts]}


@app.delete('/api/sessions/{session_id}', status_code=204)
def remove_session(session_id:uuid.UUID, owner=Depends(owner_id), db:Session=Depends(get_db)):
    row = owned(db, session_id, owner, lock=True)
    db.execute(delete(Artifact).where(Artifact.session_id==row.id))
    db.execute(delete(Message).where(Message.session_id==row.id))
    db.delete(row)
    db.commit()


@app.get('/api/library')
def library(q:str='', db:Session=Depends(get_db)):
    rows = db.scalars(select(Transcript).order_by(Transcript.guest)).all()
    return [{'id':t.id,'guest':t.guest,'title':t.title,'url':t.url} for t in rows if q.lower() in (t.guest+' '+t.title).lower()][:500]


@app.post('/api/sessions/{session_id}/messages')
def chat(session_id:uuid.UUID, body:ChatInput, owner=Depends(owner_id), db:Session=Depends(get_db)):
    prompt = body.content.strip()
    if not prompt:
        raise HTTPException(422, detail={'code':'empty_message','message':'Write a question before sending.'})
    row = owned(db, session_id, owner, lock=True)
    history = list(reversed(db.scalars(select(Message).where(Message.session_id==row.id).order_by(Message.created_at.desc(), Message.id.desc()).limit(8)).all()))
    mode = route_mode(prompt, body.mode)
    provider = body.provider or settings().llm_provider
    query = contextual_query(prompt, history)
    started = time.monotonic()
    sources = index.search(db, query, settings().retrieval_limit)
    retrieval_ms = round((time.monotonic()-started)*1000)
    artifact = None
    warnings = []
    if not sources:
        answer = "I couldn't find enough supporting material in the indexed transcripts to answer that reliably. Try naming a product topic, framework, or podcast guest. I won't fill the gap with an unsupported answer."
        details = {'sources':[], 'mode':mode, 'provider':provider, 'grounded':False, 'warnings':[]}
    else:
        previous_artifact = db.scalar(select(Artifact).where(Artifact.session_id == row.id)
                                      .order_by(Artifact.created_at.desc()).limit(1))
        model_history = generation_history(history, previous_artifact, sources)
        result = generate(mode, provider, prompt, model_history, sources, row.id)
        content = result['content'].strip()
        if mode == 'essay':
            content, _ = fit_essay(content)
        cited = verify_citations(content, sources)
        fallback_used = mode == 'ask' and bool(attribution_warnings(content, cited))
        if fallback_used:
            content = evidence_fallback(cited)
            warnings.append('A guest/source mismatch was detected. Showing transcript excerpts instead of the generated summary.')
        if mode != 'html':
            warnings.extend(quotation_warnings(content, cited))
            warnings.extend(attribution_warnings(content, cited))
        if mode == 'essay':
            count = word_count(content)
            if not 1100 <= count <= 1400:
                warnings.append(f'This draft has {count:,} words; the requested range is 1,100–1,400. Ask for a revision before publishing.')
        details = {'sources':cited, 'mode':mode, 'provider':provider, 'model':result.get('model',''),
            'grounded':True, 'response_kind':'evidence_fallback' if fallback_used else 'generated', 'warnings':warnings, 'word_count':word_count(content),
            'retrieval_ms':retrieval_ms, 'generation_ms':result.get('duration_ms',0)}
        answer = content if mode == 'ask' else ('Your essay is ready in the artifact panel.' if mode == 'essay' else 'Your document is ready in the artifact panel.')
    user = Message(session_id=row.id, role='user', content=prompt)
    db.add(user)
    db.flush()
    assistant = Message(session_id=row.id, role='assistant', content=answer, details=details)
    db.add(assistant)
    db.flush()
    if sources and mode != 'ask':
        title = re.sub(r'[#*_<>]', '', prompt)[:85].strip()
        artifact = Artifact(session_id=row.id, message_id=assistant.id, title=title,
            format='html' if mode=='html' else 'markdown', content=content, sources=details['sources'])
        db.add(artifact)
        db.flush()
        assistant.details = {**details, 'artifact_id':artifact.id}
    if row.title == 'Untitled conversation':
        row.title = prompt[:80]
    row.updated_at = now()
    db.commit()
    logger.info(json.dumps({'event':'response_complete','session_id':row.id,'mode':mode,'provider':provider,
        'source_count':len(details['sources']),'retrieval_ms':retrieval_ms,'duration_ms':round((time.monotonic()-started)*1000)}))
    return {'user':message_out(user), 'assistant':message_out(assistant),
        'artifact':artifact_out(artifact) if artifact else None, 'session':session_out(row)}


if Path('dist').is_dir():
    app.mount('/', StaticFiles(directory='dist', html=True), name='frontend')
