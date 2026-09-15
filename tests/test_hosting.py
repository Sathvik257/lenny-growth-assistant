import base64
from backend.access import GenerationGate, authorized
from backend.config import Settings, settings

def test_render_connection_normalization():
    cfg = Settings(_env_file=None, database_url='postgresql://u:p@db/db', agent_url='agent:8788')
    assert cfg.database_url == 'postgresql+psycopg://u:p@db/db'
    assert cfg.agent_url == 'http://agent:8788'

def test_production_rejects_default_secrets():
    import pytest
    with pytest.raises(ValueError):
        Settings(_env_file=None, environment='production')

def test_generation_gate_rejects_parallel_and_excess_work():
    gate = GenerationGate()
    assert gate.enter(1) is None
    assert 'Another response' in gate.enter(1)
    gate.leave()
    assert 'hourly' in gate.enter(1)

def test_basic_auth_fails_closed():
    cfg = Settings(_env_file=None, access_password='a-long-review-password')
    assert not authorized('Basic invalid%%', cfg)
    assert not authorized('Bearer ignored', cfg)
    token = base64.b64encode(b'reviewer:a-long-review-password').decode()
    assert authorized('Basic '+token, cfg)

def test_hosted_routes_protected_and_health_public(client, monkeypatch):
    monkeypatch.setattr(settings(), 'access_password', 'a-long-review-password')
    assert client.get('/api/status').status_code == 401
    assert client.get('/api/health/live').status_code == 200
    assert client.get('/api/library', auth=('reviewer', 'wrong')).status_code == 401
    assert client.get('/api/library', auth=('reviewer', 'a-long-review-password')).status_code == 200

def test_gate_released_after_failed_request(client, headers):
    from backend.access import gate
    gate.events.clear()
    response = client.post('/api/sessions/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/messages', headers=headers, json={'content':'test'})
    assert response.status_code == 404
    assert not gate.active


def test_explicit_guest_citation_mismatch_and_saved_answer_warning():
    from backend.service import attribution_warnings
    from backend.main import message_out
    from backend.db import now
    from types import SimpleNamespace
    sources = [{'label':'S1','guest':'Sean Ellis'}, {'label':'S2','guest':'Rahul Vohra'}]
    assert not attribution_warnings('[Rahul Vohra] [S2] explains it.', sources)
    content = '[Sean Ellis] [S2] explains it.'
    assert attribution_warnings(content, sources)
    saved = SimpleNamespace(id='test',role='assistant',content=content,created_at=now(),details={'sources':sources})
    assert message_out(saved)['warnings']
