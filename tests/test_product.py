import uuid
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from backend.db import Artifact, ChatSession, Message, SessionLocal
from backend.service import route_mode, verify_citations, word_count
from backend.retrieval import contextual_query, index
import backend.main as main


def create(client, headers):
    r=client.post('/api/sessions',headers=headers,json={'display_name':'Evaluator','timezone':'Asia/Kolkata'})
    assert r.status_code==201, r.text
    return r.json()['id']


def grounded(monkeypatch, text='Interview customers weekly to guide product discovery. [S1]'):
    def respond(*args):
        return {'content':text,'model':'test-model','duration_ms':10}
    monkeypatch.setattr(main,'generate',respond)


@pytest.mark.parametrize('text,expected',[
    ('What drives retention?','ask'),('Write an essay about retention','essay'),
    ('Build an HTML brief','html'),('Make a Markdown document','markdown'),
])
def test_routing(text, expected):
    assert route_mode(text)==expected


def test_explicit_route_wins():
    assert route_mode('Explain HTML', 'ask')=='ask'


def test_followup_context():
    history=[SimpleNamespace(role='user',content='How do customer interviews support product discovery?')]
    assert 'customer interviews' in contextual_query('Turn that into an essay',history)
    assert contextual_query('Explain pricing strategy for enterprise buyers',history)=='Explain pricing strategy for enterprise buyers'


def test_citation_gate():
    sources=[{'label':'S1'}]
    assert verify_citations('A claim [S1]',sources)==sources
    for content in ['A claim [S2]','No citations here','Mixed [S1] and [S99]']:
        with pytest.raises(HTTPException):
            verify_citations(content,sources)


def test_word_count_ignores_markup():
    assert word_count('<h1>Hello world</h1> [S1]')==2


def test_session_workspace_isolation(client,headers):
    sid=create(client,headers)
    other={'X-Workspace-ID':str(uuid.uuid4())}
    assert client.get('/api/sessions',headers=other).json()==[]
    assert client.get('/api/sessions/'+sid,headers=other).status_code==404
    assert client.delete('/api/sessions/'+sid,headers=other).status_code==404
    assert client.get('/api/sessions/'+sid,headers=headers).status_code==200


def test_validation(client,headers):
    sid=create(client,headers)
    assert client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':' '}).status_code==422
    assert client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':'x'*8001}).status_code==422
    assert client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':'hello','provider':'unknown'}).status_code==422
    assert client.get('/api/sessions',headers={'X-Workspace-ID':'invalid'}).status_code==422


def test_retrieval_and_no_evidence():
    with SessionLocal() as db:
        found=index.search(db,'weekly customer interviews product discovery')
        assert found and found[0]['guest']=='Test Guest'
        assert found[0]['chunk_id'] and found[0]['url']
        assert index.search(db,'quantum superconductivity neutrinos')==[]


def test_persisted_chat_and_new_session(client,headers,monkeypatch):
    grounded(monkeypatch)
    sid=create(client,headers)
    response=client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':'How do customer interviews improve product discovery?'})
    assert response.status_code==200, response.text
    body=response.json()
    assert body['assistant']['sources'][0]['label']=='S1'
    assert len(client.get('/api/sessions/'+sid,headers=headers).json()['messages'])==2
    fresh=create(client,headers)
    assert client.get('/api/sessions/'+fresh,headers=headers).json()['messages']==[]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Message))==2
        assert db.get(ChatSession,sid).user_metadata['display_name']=='Evaluator'


def test_unsupported_does_not_call_model(client,headers,monkeypatch):
    def fail(*args): raise AssertionError('Must not call model for empty retrieval')
    monkeypatch.setattr(main,'generate',fail)
    sid=create(client,headers)
    response=client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':'Explain quantum superconductivity neutrinos'})
    assert response.status_code==200
    assert response.json()['assistant']['grounded'] is False
    assert response.json()['assistant']['sources']==[]


def test_model_failure_rolls_back_turn(client,headers,monkeypatch):
    def fail(*args): raise HTTPException(504,detail={'code':'model_timeout','message':'Timed out'})
    monkeypatch.setattr(main,'generate',fail)
    sid=create(client,headers)
    r=client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':'Explain customer interviews for product discovery'})
    assert r.status_code==504
    assert r.json()['error']['code']=='model_timeout'
    assert r.headers['X-Request-ID']
    assert client.get('/api/sessions/'+sid,headers=headers).json()['messages']==[]


def test_invalid_citations_not_persisted(client,headers,monkeypatch):
    grounded(monkeypatch,'Invented citation [S99]')
    sid=create(client,headers)
    r=client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':'Explain customer interviews for product discovery'})
    assert r.status_code==502
    assert client.get('/api/sessions/'+sid,headers=headers).json()['messages']==[]


def test_artifact_persistence_and_delete(client,headers,monkeypatch):
    grounded(monkeypatch,'<html><body><h1>Customer discovery</h1><p>Interview customers weekly [S1]</p></body></html>')
    sid=create(client,headers)
    r=client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':'Create a customer interviews product discovery HTML brief','mode':'html'})
    assert r.status_code==200, r.text
    a=r.json()['artifact']
    assert a['format']=='html'
    detail=client.get('/api/sessions/'+sid,headers=headers).json()
    assert detail['artifacts'][0]['id']==a['id']
    assert client.delete('/api/sessions/'+sid,headers=headers).status_code==204
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Artifact))==0
        assert db.scalar(select(func.count()).select_from(Message))==0


def test_essay_length_warning(client,headers,monkeypatch):
    grounded(monkeypatch,'# Product discovery\n\nInterview customers every week. [S1]')
    sid=create(client,headers)
    r=client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':'Write an essay about customer interviews and product discovery','mode':'essay'})
    assert r.status_code==200
    assert r.json()['assistant']['warnings']
    assert r.json()['artifact']['format']=='markdown'


def test_named_guest_does_not_borrow_another_guests_advice(client):
    from backend.db import Chunk
    with SessionLocal.begin() as db:
        other=db.scalars(select(Chunk).where(Chunk.transcript_id=='other')).first()
        other.text='customer interviews discovery product '*100
    with SessionLocal() as db:
        found=index.search(db,'What does Test Guest say about customer interviews?')
    assert found and all(s['guest']=='Test Guest' for s in found)


def test_unverified_long_quotations_are_flagged():
    from backend.service import quotation_warnings
    sources=[{'excerpt':'The product team should interview customers every single week to learn what they need.'}]
    assert quotation_warnings('She said, "The product team should interview customers every single week to learn what they need."',sources)==[]
    assert quotation_warnings('She said, "Everyone should schedule ten interviews before any product decision is made."',sources)


def test_attribution_failure_returns_evidence_without_second_model_call(client, headers, monkeypatch):
    sources = [dict(label='S1',guest='Test Guest',excerpt='Weekly interviews reveal customer needs.'),
               dict(label='S2',guest='Other Guest',excerpt='Pricing depends on customer segments.')]
    monkeypatch.setattr(main.index,'search',lambda *args: sources)
    calls=[]
    def generate(*args):
        calls.append(args)
        return {'content':'[Test Guest] [S2] claims pricing solves everything. [S1]', 'model':'test-model'}
    monkeypatch.setattr(main,'generate',generate)
    sid=create(client,headers)
    response=client.post('/api/sessions/'+sid+'/messages',headers=headers,json={'content':'Compare customer research and pricing.'})
    assert response.status_code==200
    answer=response.json()['assistant']
    assert answer['response_kind']=='evidence_fallback'
    assert 'Weekly interviews reveal customer needs' in answer['content']
    assert 'pricing solves everything' not in answer['content']
    assert len(calls)==1
    assert client.get('/api/sessions/'+sid,headers=headers).json()['messages'][-1]['content']==answer['content']

def test_evidence_fallback_escapes_source_markup():
    from backend.service import evidence_fallback
    content=evidence_fallback([{'label':'S1','guest':'Guest','excerpt':'[fake](https://example.com) <script>bad</script>'}])
    assert '[S1]' in content
    assert '[fake](https://example.com)' not in content
    assert '<script>' not in content
