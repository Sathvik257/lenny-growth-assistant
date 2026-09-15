"""Measured corpus retrieval, no model calls or synthetic success claims."""
import json
from pathlib import Path
from backend.db import SessionLocal
from backend.retrieval import index
CASES=[
 ('How does Sean Ellis measure product market fit with a survey?','Sean Ellis'),
 ('How does Rahul Vohra improve product market fit at Superhuman?','Rahul Vohra'),
 ('How does April Dunford define positioning and competitive alternatives?','April Dunford'),
 ('What does Teresa Torres recommend for continuous discovery customer interviews?','Teresa Torres'),
 ('How does Brian Balfour describe growth loops and retention?','Brian Balfour'),
 ('What does Shreyas Doshi say about pre mortems and product strategy?','Shreyas Doshi'),
 ('How does Marty Cagan describe empowered product teams?','Marty Cagan'),
 ('What does Elena Verna say about product led growth?','Elena Verna'),
 ('What does Brian Chesky say about Airbnb product design?','Brian Chesky'),
 ('How does Julie Zhuo think about management and feedback?','Julie Zhuo'),
]
results=[]
with SessionLocal() as db:
 for query,expected in CASES:
  found=index.search(db,query)
  guests=[s['guest'] for s in found]
  results.append({'query':query,'expected_guest':expected,'retrieved_guests':guests,'hit':any(expected.lower() in g.lower() for g in guests)})
report={'scope':'Guest-anchored retrieval; does not measure semantic answer correctness or unanchored paraphrase recall.','cases':results,'hits':sum(r['hit'] for r in results),'total':len(results)}
Path('docs').mkdir(exist_ok=True)
Path('docs/retrieval-results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
