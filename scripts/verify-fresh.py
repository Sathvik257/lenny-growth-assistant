"""Check a separate installed source copy against a new, isolated PostgreSQL database."""
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient


def main():
    # Local developer credentials from .env.example. Never touch the application database.
    admin = create_engine('postgresql+psycopg://lenny:lenny_local_only@127.0.0.1:54329/postgres',
                          isolation_level='AUTOCOMMIT', connect_args={'connect_timeout':5})
    database = 'lenny_fresh_' + uuid.uuid4().hex[:12]
    with admin.connect() as connection:
        connection.execute(text('CREATE DATABASE ' + database + " ENCODING 'UTF8' TEMPLATE template0"))
    os.environ['DATABASE_URL'] = 'postgresql+psycopg://lenny:lenny_local_only@127.0.0.1:54329/' + database
    subprocess.run([sys.executable, 'scripts/fetch-transcripts.py', '--limit', '3', '--revision',
                    'be8ab89a890a833cbba2c892178f823fff178c65'], check=True, timeout=120)
    subprocess.run([sys.executable, '-m', 'backend.ingest'], check=True, timeout=120)
    from backend.main import app
    headers = {'X-Workspace-ID':str(uuid.uuid4())}
    with TestClient(app) as client:
        assert client.get('/').status_code == 200
        ready = client.get('/api/health/ready').json()
        assert ready['transcripts'] == 3
        created = client.post('/api/sessions', headers=headers, json={'display_name':'Fresh setup check','timezone':'UTC'})
        assert created.status_code == 201
        session = created.json()['id']
        response = client.post('/api/sessions/' + session + '/messages', headers=headers,
                               json={'content':'zzquasarxx flibbertigibbetxyz','provider':'ollama'})
        assert response.status_code == 200 and not response.json()['assistant']['sources']
    with TestClient(app) as reopened:
        assert len(reopened.get('/api/sessions/'+session, headers=headers).json()['messages']) == 2
        assert reopened.delete('/api/sessions/'+session, headers=headers).status_code == 204
    report = {'database':database,'transcripts':3,'frontend_http':200,'persistence_across_clients':True,
              'unsupported_query':True,'scope':'Fresh dependencies and source copy; existing PostgreSQL service; no generated AI answer in this check'}
    Path('.runtime').mkdir(exist_ok=True)
    Path('.runtime/fresh-setup-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
