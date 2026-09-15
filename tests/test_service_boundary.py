from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from backend import service


@pytest.mark.parametrize('status,payload,expected', [(200, [], 502), (200, {'content':''}, 502), (503, [], 503)])
def test_malformed_agent_response_is_a_structured_failure(monkeypatch, status, payload, expected):
    monkeypatch.setattr(service.httpx, 'post', lambda *args, **kwargs:
                        SimpleNamespace(status_code=status, json=lambda:payload))
    with pytest.raises(HTTPException) as failure:
        service.generate('ask','ollama','question',[],[])
    assert failure.value.status_code == expected
    assert failure.value.detail['code']
