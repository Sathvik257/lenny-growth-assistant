"""Bounded, inspectable lexical RAG with source diversity and immutable citations."""
import re
import math
import threading
from collections import Counter
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from .db import Chunk, Transcript

STOP = set('a an the is are was were be been being to for from in on at by with of and or but how what why when which who can could should would do does did i we you my our your it its this that these those me tell about please write create generate essay markdown html artifact document turn into make give use based using explain more'.split())


def tokens(text):
    return [w for w in re.findall(r'[a-z0-9]+', text.lower()) if len(w) > 2 and w not in STOP]


def contextual_query(query, history):
    """Expand referential follow-ups only; don't contaminate new topics."""
    referential = re.search(r'\b(that|this|those|it|they|them|above|previous|same|expand|elaborate)\b', query, re.I)
    if referential or len(tokens(query)) < 3:
        prior = [m.content for m in history if m.role == 'user'][-2:]
        return ' '.join(prior + [query])[-1800:]
    return query


class Index:
    def __init__(self):
        self.lock = threading.RLock()
        self.rows = []
        self.bm25 = None
        self.guests = set()
        self.intros = []
        self.ads = []

    def refresh(self, db):
        rows = db.execute(select(Chunk, Transcript).join(Transcript)).all()
        corpus = [tokens(c.text) for c, t in rows]
        with self.lock:
            self.rows = rows
            self.guests = {t.guest for _, t in rows}
            self.intros = [bool(re.search(r'(?i)subscribe and follow|brought to you by|episode is for you|welcome to the podcast', c.text)) for c, _ in rows]
            self.ads = [bool(re.search(r'(?i)\bsponsor(?:ed|s)?\b|brought to you by|sign up|free trial|try.{0,60}free|use (?:the )?code|dovetailapp\.com', c.text)) for c, _ in rows]
            self.bm25 = BM25Okapi(corpus) if corpus else None
            if self.bm25:
                frequencies = Counter(word for doc in corpus for word in set(doc))
                self.bm25.idf = {word: math.log(1 + (len(corpus)-df+0.5)/(df+0.5)) for word, df in frequencies.items()}

    def search(self, db, query, limit=5):
        with self.lock:
            if self.bm25 is None:
                self.refresh(db)
        q = tokens(query)
        if not q:
            return []
        with self.lock:
            if self.bm25 is None:
                return []
            # Guest names identify an episode; repeated speaker labels must not dominate relevance.
            named = {guest for guest in self.guests if guest.lower() in query.lower()}
            name_tokens = {w for guest in named for w in tokens(guest)}
            topical = [w for w in q if w not in name_tokens] or q
            scores = self.bm25.get_scores(topical)
            for i, (chunk, transcript) in enumerate(self.rows):
                if named:
                    scores[i] *= 2.5 if transcript.guest in named else 0.65
                # Introductions and sponsor reads often repeat topic keywords without evidence.
                if self.intros[i]:
                    scores[i] *= 0.25
            ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            found, counts = [], Counter()
            for i in ranked:
                c, t = self.rows[i]
                if named and t.guest not in named:
                    continue
                overlap = set(q) & set(tokens(f'{t.guest} {t.title} {c.text}'))
                # Require two distinct terms for multi-term questions; score is relevance, not confidence.
                if scores[i] < 1.5 or len(overlap) < min(2, len(set(q))) or counts[t.id] >= 2:
                    continue
                if self.ads[i]:
                    continue
                counts[t.id] += 1
                found.append({'label': f'S{len(found)+1}', 'chunk_id': c.id, 'guest': t.guest,
                    'title': t.title, 'url': t.url, 'youtube_url': t.youtube_url,
                    'timestamp': c.timestamp, 'excerpt': c.text, 'score': round(float(scores[i]), 2)})
                if len(found) == limit:
                    break
            return found


index = Index()
