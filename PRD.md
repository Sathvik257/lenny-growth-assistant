# Lenny Growth Assistant

## Discovery brief

The primary user is a product manager or growth lead preparing a decision, experiment, or internal narrative. They have access to valuable interviews but lack the time to find the relevant passages and turn them into usable work. This product connects a question to evidence, then to a reusable document without leaving the conversation.

The product is a local research studio with three explicit modes: Ask, Write an essay, and Create an artifact. Source passages remain inspectable beside the work. An answer is a starting point for judgment, not a substitute for reading the source.

## Success criteria

- A fresh evaluator can follow the README to start the system without code changes, excluding model and transcript download time.
- Every supported answer contains valid citations resolving to retrieved transcript passages; unsupported questions produce a clear limitation.
- A curated ten-question retrieval set reaches a relevant guest in the top five results for at least eight questions. Record measured results; do not claim this target is already achieved.
- Chats survive an API restart and remain isolated by session and browser workspace identifier.
- Essays target 1,250 words, with an accepted range of 1,100–1,400; deviations are visible rather than silently treated as success.
- HTML artifact scripts and network requests cannot execute in the viewer.

## Assumptions and scope

This is an internal, single-machine evaluation with anonymous browser workspaces. Browser identifiers separate workspaces but are not production authentication. PostgreSQL is the system of record. Ollama is the default and required demo provider; Anthropic is an explicit optional cloud choice. Local-to-cloud fallback is never automatic. Transcript retrieval uses BM25 to keep operation inspectable and avoid a second embedding model on memory-constrained hardware.

Included: ingestion and refresh CLI, persisted sessions, context-aware retrieval, citations, dedicated essay skill, Markdown and HTML artifacts, responsive viewer, provider configuration, structured errors/logs, health endpoints, meaningful tests, reproducible startup and handoff.

Excluded: team accounts, billing, arbitrary uploads, live web browsing, autonomous shell/file tools, model fine-tuning, collaborative editing and public internet deployment. These do not improve the core evaluation flow enough to justify their cost within the assignment.

## Flows and acceptance criteria

1. User creates a chat, asks a growth question, sees a loading state, then a cited answer. The evidence panel opens passages and upstream links. Follow-up questions use only that session's recent context.
2. User selects essay mode. The agent applies the versioned writing skill and returns a Markdown artifact with word count, citations and actionable conclusion. The agent builds an opening, five body sections and a takeaway, measuring length between sections; one additional section may address a short draft. Any remaining deviation is shown.
3. User requests an HTML artifact. It renders in an isolated iframe alongside chat. The user can inspect source and download the artifact.
4. User starts a new chat. Previous messages disappear from the active conversation and remain available in history.
5. Ollama is unavailable, a key is missing, retrieval is empty, or PostgreSQL fails. The app reports a specific next action and does not fabricate content or lose previously saved work.

## Risks and decisions

Small local models may be slower and less faithful than cloud models. Validate citation labels deterministically, use short bounded evidence and expose passages; semantic correctness still needs evaluation. BM25 can miss paraphrases; add embeddings only after a measured retrieval gap. Transcripts can include hostile instructions; treat them as quoted evidence and give the model no filesystem or shell tools. Generated HTML is untrusted and receives both sanitization and a scriptless, network-blocked iframe. Logs contain identifiers and timings rather than prompts or secrets. Public deployment requires real authentication, authorization, TLS and rate limits before exposure.

## Implementation plan

First prove Pi with local/cloud configuration, then implement PostgreSQL and retrieval, then the three product modes and UI, then integration/security tests, and finally the fresh-start handoff and camera demo.
