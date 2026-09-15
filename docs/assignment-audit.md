# Assignment compliance audit — updated 15 September 2026

## Latest update

The public repository now exists at https://github.com/Sathvik257/lenny-growth-assistant. Source publication and the GitHub Actions outcome are checked in the final handoff. The historical matrix below records earlier gaps; the following changes supersede those entries:

- Artifact follow-ups now include a bounded excerpt of the prior document, with citation labels remapped to current evidence.
- Native startup identifies this project before reusing a server and skips occupied ports, preventing an unrelated app from appearing as this preview.
- Fresh Python/Node dependencies were installed in an isolated source copy. Its build and tests passed. Three real transcripts were downloaded into a new database; API readiness, session creation, an unsupported query, persistence across API clients and cleanup passed. Existing PostgreSQL was reused; this is same-machine verification, not a second-machine or Docker demonstration.
- A GitHub Actions workflow checks PostgreSQL persistence, agent/startup behavior, HTML sanitization and the frontend build.

The YouTube camera demo, submission form, actual cloud-provider generation and full semantic reliability are still outstanding. The app does not guarantee factual correctness merely because a citation is valid.

Compared against the full assignment supplied in pasted-text.txt. This report distinguishes existing implementation from verified behavior and external deliverables. The orange frontend was not modified.

## Important interpretation
The engagement explicitly asks for deploying locally, and the demo must run Ollama. A publicly hosted application URL is not listed as a deliverable. Render/Vercel hosting is optional. A public GitHub repository and a YouTube demo are mandatory.

## Requirement-by-requirement evidence

| Assignment requirement | Evidence in this project | Status / remaining work |
|---|---|---|
| Discovery: primary user, problem, pain | PRD.md discovery brief | Present |
| Measurable success metric | PRD.md success criteria: retrieval target, essay range, persistence and startup | Present; targets are not universal performance guarantees |
| Assumptions, scope exclusions and rationale | PRD.md assumptions and scope | Present |
| Risks/trade-offs | PRD.md risks; architecture.md limits | Present |
| Discovery before implementation | Curated chronology in agent-transcripts/README.md | Recorded; independent historical proof not established |
| FastAPI backend | backend/main.py | Implemented and tested |
| Claude Agent SDK or Pi Coding Agent | agent/server.mjs uses @earendil-works/pi-coding-agent | Pi integration implemented; real Ollama generations recorded |
| New chats and independent context | Session ownership, bounded per-session history, new-conversation control | Implemented; isolation and persistence tests passed |
| PostgreSQL conversations, IDs, timestamps, metadata | backend/db.py; creation metadata includes display name/timezone | Implemented; PostgreSQL suite passed |
| Request/response contracts, validation, errors, health | Pydantic request schemas, documented API, /docs, structured errors and health endpoints | Present; responses use documented JSON shapes rather than exhaustive response models |
| At least one cloud provider | Anthropic through Pi; configurable key/model | Implemented, but successful cloud generation NOT verified: no key supplied |
| Ollama local demo | qwen2.5:3b; real Q&A, essay and HTML results | Local operation verified; mandatory recorded video still missing; CPU latency is substantial |
| Visible provider selection; no-code configuration; fallback behavior | UI provider control, .env.example, README | Present; no automatic cloud fallback |
| Actual Lenny transcript ingestion | 303 transcripts / 23,178 chunks; fetch and ingest scripts | Verified locally |
| Chunking, indexing, refresh, source tracing explained | architecture.md; hashes, recorded revision, source URLs and timestamps | Present; source URLs follow upstream main, manifest records download revision |
| Grounded product/growth answers with citations | BM25 retrieval, citation gate, source viewer | Implemented; semantic accuracy only PARTIAL: observed misattributions remain possible |
| Follow-ups and session context | Contextual query expansion and bounded message history | Implemented; automated coverage; not an unlimited-memory conversation system |
| Acknowledge unsupported questions | Empty-retrieval limitation response | Live probe verified; this is not broad proof of out-of-domain detection |
| Dedicated Ship 30 skill based on guide | skills/ship-30/SKILL.md cites guide and encodes writing principles | Present; actual runtime skill routing tested |
| Approximately 1,250 words | Section drafting and length checks; recorded 1,360-word result | Demonstrated once; all requests are not guaranteed to meet target |
| Hook, progression, headings, bullets, selective bold, useful takeaway | Skill and drafting instructions | Implemented; latest prompt formatting adjustment not fully demonstrated by a new live essay |
| Essay claims grounded in transcripts | Retrieved evidence, citations, quotation warnings | PARTIAL: manual review found quotation/attribution problems; review generated content |
| Markdown and HTML/CSS artifacts using conversation | Artifact modes, bounded history, stored artifact records | Implemented; history is truncated and prior artifact bodies are not fully replayed for revisions |
| Artifact viewer beside chat | src/App.tsx, source/preview/download controls | Desktop side panel and narrow-screen overlay inspected; frontend retained unchanged |
| Untrusted HTML isolation/sanitization explained and implemented | src/security.ts, empty iframe sandbox, CSP, architecture.md | Four sanitizer tests and prior browser script probe passed; not a complete security audit |
| Practical one-command startup | start.ps1; Docker Compose setup | Present; prepared Windows startup exercised, fresh-machine workflow and Docker execution NOT verified |
| Safe .env.example; no secrets committed | .env.example, ignore rules, explicit source-only archive | Archive excludes .env/runtime/dependencies; public Git history does not exist yet and must be checked when publishing |
| Structured logs and diagnostic visibility | API request IDs/status/timing; model/retrieval events; UI error handling | Present; artifact security tests cover rendering safeguards, no centralized browser telemetry |
| Missing keys, unavailable model, timeouts, empty retrieval, database errors | backend/service.py, exception handlers, agent deadline, live checks | Implemented; missing-key/empty-retrieval/rollback live checks passed; not every failure re-injected in the final run |
| Run/test/troubleshoot/extend handoff | README, architecture, manual test plan, evaluator guide | Present; clean-clone verification remains outstanding |
| Public GitHub source repository | https://github.com/Sathvik257/lenny-growth-assistant | Published; initial GitHub Actions run 34956514354 passed |
| README with all requested topics | README.md | Present |
| PRD with flows, acceptance criteria and plan | PRD.md | Present |
| design.md with UX, states, responsiveness, accessibility | design.md | Present; full accessibility audit not established |
| architecture.md with schema/API/security/topology | architecture.md | Present |
| Coding-agent transcripts/logs and failed attempts | agent-transcripts/ curated chronology and actual test logs | Present as curated logs; not a full conversation export. Include export if requested by evaluator |
| Meaningful tests and manual UI plan | tests/, agent/*.test.mjs, src/security.test.ts, docs/manual-test-plan.md | Latest backend: 32 passed on SQLite/PostgreSQL. Unchanged agent: 6 passed; sanitizer: 4 passed |
| 2–3 minute camera-enabled YouTube demo | docs/demo-script.md provides plan only | MISSING: record real local Ollama demo and upload |
| Submission form | Link in START_HERE.md and README | NOT submitted |
| Deadline | Assignment says 15/09/26 EOD | 15 September 2026; timezone unspecified |

## Work remaining before submission

1. Review a successful local Q&A, essay and HTML artifact against their cited excerpts; prepare outputs before recording. The small local model's semantic accuracy is the largest product weakness.
2. Test the documented startup from a clean extracted source folder or another machine. Existing prepared-workspace tests are not a substitute for this acceptance criterion.
3. If you can supply an Anthropic API key, exercise a successful cloud question and artifact. The code integration is present, but missing-key behavior alone does not prove it works.
4. Public GitHub publication is complete. Keep secrets and runtime data excluded from future commits.
5. Record the required 2–3 minute camera-on local Ollama demo, upload to YouTube and verify evaluator access.
6. Submit the repository/video links through https://forms.gle/LgotDHNVxW1mbzNE7 by the stated deadline.

## Conclusion
The main application and documentation components are present and the public source repository is published. All 50 automated checks passed locally and the initial GitHub Actions run passed. Fresh dependencies and an isolated database were verified on this machine; a separate-machine or Docker deployment remains untested. The recorded video and form submission are still pending, cloud success remains unverified, and strict semantic grounding is not guaranteed. Do not label every assignment requirement as passed.
