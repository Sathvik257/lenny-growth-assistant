from backend.ingest import parse, chunks, ingest
from backend.db import SessionLocal, Transcript, Chunk
from sqlalchemy import select, func


def test_parser_and_timestamp():
    meta,body=parse('---\nguest: Ada\ntitle: Discovery\n---\nAda (00:12:30): '+('interview customers weekly '*100))
    assert meta['guest']=='Ada'
    parts=list(chunks(body))
    assert len(parts)>1
    assert parts[0][1]=='00:12:30'


def test_ingest_idempotent_and_refresh(tmp_path):
    f=tmp_path/'ada'/'transcript.md'
    f.parent.mkdir()
    f.write_text('---\nguest: Ada\ntitle: Discovery\n---\n'+('customer interviews weekly '*200))
    assert ingest(tmp_path)==1
    assert ingest(tmp_path)==0
    with SessionLocal() as db:
        before=db.scalar(select(func.count()).select_from(Chunk).where(Chunk.transcript_id=='ada'))
        old_hash=db.get(Transcript,'ada').content_hash
    f.write_text(f.read_text()+' More insight.')
    assert ingest(tmp_path)==1
    with SessionLocal() as db:
        assert db.get(Transcript,'ada').content_hash!=old_hash
        assert db.scalar(select(func.count()).select_from(Chunk).where(Chunk.transcript_id=='ada'))==before
