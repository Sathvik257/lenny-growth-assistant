# Evaluator guide

## The problem this project addresses
Product advice is easy to generate and hard to verify. This studio keeps the original transcript evidence next to the answer and turns useful findings into saved, downloadable documents.

## What distinguishes this implementation
- Inspectable evidence: real podcast excerpts, source links, guest metadata and timestamps accompany the output.
- Deliberate failure behavior: missing citations are rejected, unavailable evidence produces a limitation, and explicit guest/source mismatches in new Q&A responses trigger a source-excerpt fallback instead of retaining the faulty summary.
- Local-first demonstration with an explicit cloud switch: there is no silent paid-provider fallback.
- Measured writing trade-offs: the Ship 30 skill uses isolated section drafting, conservative length editing and visible quality warnings.
- Durable successful work: PostgreSQL stores conversations and artifacts; failed turns roll back.
- Isolated HTML: generated previews and downloads use sanitization and restrictive sandboxing.

These are concrete engineering choices, not a claim that no other project has similar features.

## Suggested three-minute review
1. Open a saved answer and inspect one supporting passage.
2. Open the essay and HTML artifact in the same conversation; switch between preview and source.
3. Reopen the conversation to demonstrate persistence.
4. Explain the explicit provider choice and show local Ollama status.
5. Point to the tests and the recorded semantic failures, including the fallback introduced in response.

Prepare long local generations before recording. Do not present the source-excerpt fallback as a complete synthesized answer.

## Trade-offs to discuss honestly
Lexical retrieval is inexpensive and inspectable but misses paraphrases. Small CPU models are slow and can misattribute evidence. The mismatch detector recognizes only explicit bracketed guest/citation pairs; it does not verify every claim or every speaker inside an episode. Cloud model execution remains unverified without credentials. Reviewer access and rate limiting target a single-instance demo, not a multi-tenant service.

Read PRD.md, architecture.md, design.md and docs/verification.md before the interview. Be prepared to explain the code and the AI assistance used to build it.
