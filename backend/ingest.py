"""python -m backend.ingest [--path PATH]. Idempotent refresh, one transaction."""
import argparse
import hashlib
import re
from pathlib import Path
from urllib.parse import quote
import yaml
from sqlalchemy import delete, select
from .config import settings
from .db import Base, Chunk, SessionLocal, Transcript, engine, now


def parse(text):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.S)
    if match:
        return yaml.safe_load(match[1]) or {}, match[2]
    return {}, text


def chunks(body, size=240, overlap=40):
    words = body.split()
    for start in range(0, len(words), size-overlap):
        text = ' '.join(words[start:start+size])
        if len(text) < 80:
            continue
        stamp = re.search(r'\(?\b(\d{1,2}:\d{2}:\d{2})\b\)?', text)
        yield text, stamp[1] if stamp else ''


def ingest(path):
    files = sorted(Path(path).rglob('transcript.md'))
    if not files:
        raise SystemExit(f'No transcript.md files in {path}. Run scripts/fetch-transcripts.py first.')
    Base.metadata.create_all(engine)
    changed = 0
    with SessionLocal.begin() as db:
        for f in files:
            text = f.read_text(encoding='utf-8')
            digest = hashlib.sha256(text.encode()).hexdigest()
            ident = f.parent.name
            existing = db.get(Transcript, ident)
            if existing and existing.content_hash == digest:
                continue
            meta, body = parse(text)
            if existing:
                db.execute(delete(Chunk).where(Chunk.transcript_id == ident))
            record = existing or Transcript(id=ident)
            record.guest = str(meta.get('guest', ident.replace('-', ' ').title()))
            record.title = str(meta.get('title', record.guest))
            record.url = f'https://github.com/ChatPRD/lennys-podcast-transcripts/blob/main/episodes/{quote(ident)}/transcript.md'
            record.youtube_url = str(meta.get('youtube_url', ''))
            record.content_hash = digest
            record.indexed_at = now()
            db.add(record)
            db.flush()
            for pos, (part, stamp) in enumerate(chunks(body)):
                db.add(Chunk(transcript_id=ident, position=pos, text=part, timestamp=stamp))
            changed += 1
    print(f'Indexed {changed} changed transcripts; {len(files)} files inspected. Restart API to refresh its index.')
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default=settings().transcript_dir)
    ingest(parser.parse_args().path)
