"""Live infrastructure smoke check; uses its own temporary conversation."""
import json, uuid, time
from pathlib import Path
import httpx
base='http://127.0.0.1:8000'
headers={'X-Workspace-ID':str(uuid.uuid4())}
report={}
with httpx.Client(base_url=base,headers=headers,timeout=45) as c:
    r=c.get('/api/health/ready'); r.raise_for_status(); report['ready']=r.json()
    r=c.get('/api/status'); r.raise_for_status(); report['status']=r.json()
    r=c.post('/api/sessions',json={}); r.raise_for_status(); sid=r.json()['id']
    try:
        r=c.post('/api/sessions/'+sid+'/messages',json={'content':'zzquasarxx flibbertigibbetxyz','provider':'ollama'})
        assert r.status_code==200, r.text
        report['unsupported']={'http':r.status_code,'answer':r.json()['assistant']['content'],'sources':r.json()['assistant'].get('sources')}
        before=c.get('/api/sessions/'+sid).json()['messages']
        r=c.post('/api/sessions/'+sid+'/messages',json={'content':'Explain continuous discovery customer interviews','provider':'anthropic'})
        report['cloud_without_key']={'http':r.status_code,'error':r.json()}
        assert r.status_code==503 and r.json()['error']['code']=='missing_key',r.text
        after=c.get('/api/sessions/'+sid).json()['messages']
        assert len(before)==len(after)
        report['failed_turn_rollback']=True
    finally:
        c.delete('/api/sessions/'+sid).raise_for_status()
Path('docs/live-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
