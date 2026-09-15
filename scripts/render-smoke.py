"""Exercise the real free-tier container without buying model API usage."""
import base64
import json
import os
import time
import urllib.request
import uuid

url = os.environ.get('SMOKE_URL', 'http://127.0.0.1:18080')
headers = {'Authorization': 'Basic ' + base64.b64encode(f"reviewer:{os.environ['ACCESS_PASSWORD']}".encode()).decode(),
           'Content-Type': 'application/json', 'X-Workspace-ID': str(uuid.uuid4())}


def request(path, method='GET', body=None):
    req = urllib.request.Request(url + path, headers=headers, method=method,
                                 data=None if body is None else json.dumps(body).encode())
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()
        return json.loads(data) if path.startswith('/api/') else data


deadline = time.monotonic() + 600
while True:
    try:
        ready = request('/api/health/ready')
        break
    except OSError:
        if time.monotonic() > deadline:
            raise RuntimeError('Container readiness deadline exceeded.')
        time.sleep(2)
assert ready['transcripts'] == 40, ready
assert b'<html' in request('/').lower()
status = request('/api/status')
assert status['database'] and status['agent'], status
session = request('/api/sessions', 'POST', {})['id']
try:
    result = request(f'/api/sessions/{session}/messages', 'POST',
                     {'content': 'zqxjvplm zzqxxv', 'mode': 'ask', 'provider': 'anthropic'})
    assert result['assistant']['grounded'] is False
    assert len(request(f'/api/sessions/{session}')['messages']) == 2
finally:
    request(f'/api/sessions/{session}', 'DELETE')
print('Free container passed: frontend, 40 real transcripts, agent, retrieval, persistence and cleanup.')
