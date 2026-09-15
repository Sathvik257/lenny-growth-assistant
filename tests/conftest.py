import os
from pathlib import Path
import tempfile
import pytest
import uuid

Path(".runtime").mkdir(exist_ok=True)

def pytest_configure(config):
    if config.option.basetemp is None:
        config.option.basetemp = str(Path(".runtime") / ("pytest-" + uuid.uuid4().hex))

test_url = os.environ.get('TEST_DATABASE_URL', '')
if test_url:
    if not test_url.rsplit('/', 1)[-1].endswith('_test'):
        raise RuntimeError('Integration test database must end in _test')
    os.environ['DATABASE_URL'] = test_url
else:
    os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(tempfile.mkdtemp(dir=".runtime")) / 'tests.sqlite')
    os.environ['ALLOW_SQLITE'] = 'true'
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import Base, engine, SessionLocal, Transcript, Chunk
from backend.retrieval import index


@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal.begin() as db:
        db.add(Transcript(id='test-guest', guest='Test Guest', title='Product discovery and retention',url='https://example.com/transcript',youtube_url='',content_hash='a'*64))
        db.flush()
        db.add(Chunk(transcript_id='test-guest',position=0,text='Product discovery starts with weekly customer interviews. Teams improve retention by understanding customer needs and testing their assumptions before building features. '*4,timestamp='00:12:00'))
        db.add(Transcript(id='other',guest='Other Guest',title='Pricing',url='https://example.com/other',content_hash='b'*64))
        db.flush()
        db.add(Chunk(transcript_id='other',position=0,text='Pricing and packaging help buyers compare value. Willingness to pay can differ between customer segments. '*4))
    index.rows = []
    index.bm25 = None
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def headers():
    return {'X-Workspace-ID':'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'}
