import re
import httpx
from fastapi import HTTPException
from .config import settings

MODES = ('ask', 'essay', 'markdown', 'html')


def route_mode(text, requested='auto'):
    if requested != 'auto':
        return requested
    if re.search(r'\b(html|webpage|web page|html/css)\b', text, re.I):
        return 'html'
    if re.search(r'\b(essay|ship 30)\b', text, re.I):
        return 'essay'
    if re.search(r'\b(markdown|document|one.pager|brief|artifact)\b', text, re.I):
        return 'markdown'
    return 'ask'


def generate(mode, provider, prompt, history, sources, session_id=None):
    cfg = settings()
    if provider == 'anthropic' and not cfg.anthropic_api_key:
        raise HTTPException(503, detail={'code': 'missing_key', 'message': 'Add ANTHROPIC_API_KEY to .env and restart the services, or select Ollama.'})
    try:
        response = httpx.post(cfg.agent_url + '/generate', json={
            'mode': mode, 'provider': provider, 'prompt': prompt,
            'session_id': session_id,
            'history': [{'role': m.role, 'content': m.content} for m in history[-6:]],
            'sources': sources,
        }, headers={'Authorization': 'Bearer ' + cfg.agent_token}, timeout=cfg.model_timeout_seconds + 15)
        if response.status_code != 200:
            payload = response.json()
            if not isinstance(payload, dict):
                payload = {}
            raise HTTPException(response.status_code if response.status_code in (429, 503, 504) else 502,
                detail={'code': payload.get('code', 'model_error'), 'message': payload.get('message', 'The model could not complete this request. Try again.')})
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get('content'), str) or not payload['content'].strip():
            raise HTTPException(502, detail={'code':'invalid_model_response', 'message':'The model returned an invalid response. Please retry.'})
        return payload
    except httpx.TimeoutException:
        raise HTTPException(504, detail={'code': 'model_timeout', 'message': 'The model took too long. Try a shorter request or a smaller local model.'})
    except (httpx.RequestError, ValueError):
        raise HTTPException(503, detail={'code': 'agent_unavailable', 'message': 'The agent service is unavailable. Start it with npm run agent.'})


def verify_citations(content, sources):
    labels = set(re.findall(r'\[S(\d+)\]', content))
    allowed = {s['label'][1:] for s in sources}
    if not labels or not labels.issubset(allowed):
        raise HTTPException(502, detail={'code': 'citation_check_failed',
            'message': 'The model did not provide valid source citations. Please retry or choose a stronger model.'})
    return [s for s in sources if s['label'][1:] in labels]


def word_count(content):
    clean = re.sub(r'<[^>]+>|\[S\d+\]', ' ', content)
    return len(re.findall(r"\b[\w]+(?:['â€™-][\w]+)*\b", clean))


def quotation_warnings(content, sources):
    def normalized(value):
        return ' '.join(re.findall(r"[\w]+", value.lower()))
    evidence=[normalized(s['excerpt']) for s in sources]
    quotes=re.findall(r'["“]([^"”]{35,})["”]', content)
    if any(len(quote.split())>=8 and not any(normalized(quote) in passage for passage in evidence) for quote in quotes):
        return ['Some quoted text could not be matched verbatim to the retrieved passages. Verify or paraphrase it before reuse.']
    return []


def attribution_warnings(content, sources):
    """Flag explicit [Guest] [S1] mismatches; not a semantic accuracy guarantee."""
    guests = {s['label']: s['guest'].casefold().strip() for s in sources}
    known = set(guests.values())
    pairs = re.findall(r'\[([^\]\n]+)\]\s*\[(S\d+)\]', content)
    if any(name.casefold().strip() in known and guests.get(label) != name.casefold().strip() for name, label in pairs):
        return ['A named guest does not match the cited episode. Check the source passages before relying on this attribution.']
    return []


def evidence_fallback(sources):
    """Use source text, not another model call, after a detected attribution failure."""
    def escape(value):
        return re.sub(r'([\\`*_{}\[\]()<>#+.!|~-])', r'\\\1', value)
    parts = ["I couldn't reliably attribute the generated answer. Here are the retrieved passages instead; these excerpts are evidence, not a synthesized answer."]
    for source in sources:
        excerpt = source['excerpt']
        shortened = len(excerpt) > 900
        if shortened:
            excerpt = excerpt[:900].rsplit(' ', 1)[0]
        parts.append('**Episode guest: ' + escape(source['guest']) + '** [' + source['label'] + ']\n\n' +
            '\n'.join('> ' + escape(line) for line in excerpt.splitlines()) +
            ('\n\n*Excerpt shortened. Open the source for the full passage.*' if shortened else ''))
    return '\n\n'.join(parts)
