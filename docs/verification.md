# Verification record

## Final local-only recheck

After removing hosting-provider files, all 50 automated checks passed again: 37 PostgreSQL/backend tests, nine agent/startup tests and four sanitizer tests. The live API was healthy with 303 transcripts and 23,178 chunks, PostgreSQL and Pi available, and the local qwen2.5:3b model available. A new independent session successfully saved an unsupported-query exchange, returned both messages on reload, and was deleted with HTTP 204. No new model-generated answer or essay was requested in this recheck. Cloud generation, the recorded video and form submission remain pending. The orange frontend is unchanged.

## Latest verification — 15 September 2026

37 backend tests passed on PostgreSQL and in a fresh SQLite environment; 9 agent/startup tests and 4 sanitizer tests passed (50 checks total). The frontend production build passed with freshly installed Node dependencies, and pip check found no broken Python requirements. The fresh Node installation reported zero known vulnerabilities. Frontend source hashes remained unchanged.

An isolated source copy with new Python and Node dependencies downloaded three real transcripts at the pinned revision, imported them into a new PostgreSQL database, served the built frontend, created a conversation, handled an unsupported query, reopened saved messages through a new API client and deleted that temporary conversation. It reused this computer's PostgreSQL service. The service was initially stopped and had to be restarted before this check passed. This does not establish a new-machine or Docker install, nor a new AI generation.

Fixed two concrete gaps: bounded prior artifact text now reaches follow-up generation with remapped citation labels, and the native launcher skips other apps' occupied ports. Malformed agent responses now produce structured API failures. Added regressions and a GitHub Actions workflow. Successful cloud generation and Docker image execution remain unverified.

Development environment: Windows, Python 3.12, Node 24.18.0, portable PostgreSQL 18.4, Ollama 0.34.0, qwen2.5:3b on CPU. Docker is not installed on this machine.

## Checks completed

| Check | Result | Scope |
|---|---|---|
| Production frontend build | Passed | TypeScript checking and Vite asset build |
| Backend suite | 23 passed | Latest full run on the dedicated PostgreSQL test database; the original 19-test suite also passed on SQLite |
| Pi prompt/essay/cache tests | 6 passed | Mode-specific skill loading, data boundaries, artifact instructions, incomplete-section rejection, scaffolding cleanup and recovery-cache isolation |
| HTML sanitizer tests | 4 passed | Hostile tags/handlers, safe CSS, CSP insertion, malformed markup |
| npm dependency audit | 0 reported vulnerabilities | Audit at development time; not a guarantee against undiscovered issues |
| Corpus ingestion | 303 transcripts / 23,178 chunks | Real upstream files, recorded revision be8ab89a890a833cbba2c892178f823fff178c65 |
| Guest-anchored retrieval | 10/10 hits in top 5 | Earlier narrow benchmark before final guest/ad filtering, not answer accuracy; see retrieval-results.json |
| Live PostgreSQL/API readiness | Passed | See live-checks.json |
| Empty-retrieval behavior | Passed | Nonsense-token probe returns a limitation and no citations; not a broad out-of-domain benchmark |
| Missing cloud key | Passed | Structured 503 and no failed turn saved |
| Browser layout | Inspected | Desktop and narrow viewport, composer, evidence overlay and close control |
| Keyboard help dialog | Passed | Focus enters dialog; Escape dismisses it |
| Browser HTML isolation fixture | Passed for script probe | Production sanitizer retained safe heading and removed hostile content; script message did not execute. Empty sandbox attribute verified. Network blocking is backed by CSP/configuration tests, not a full network audit. |

Actual command logs are in ../agent-transcripts/. Backend tests emit dependency deprecation warnings; assertions pass.

## Live generation findings

A real local Q&A request completed in 206 seconds and persisted with clickable citations. Manual review found an inverted percentage and an unhelpful introductory citation. This is a semantic failure despite valid citation labels. Retrieval was adjusted to reduce speaker-name dominance and downweight introductions, and generation instructions were tightened.

The original single-pass essay plus revision completed in 784 seconds but produced only 912 words, with weak attribution and an invented book title. The UI correctly showed the length warning. That approach was replaced with section-based composition, and episode titles were removed from model evidence headers.

An initial section-based run exposed another failure: later sections collapsed to bare headings. Generation now uses fresh Pi sessions per section, rejects incomplete sections, restricts explicit guest queries to that guest’s episodes, and edits overly long drafts at paragraph boundaries. The final live essay produced 1,360 words in 391 seconds; the HTML artifact produced 106 words in 80 seconds. Both persisted and reopened in the artifact viewer. The HTML preview was visually inspected with a visible title and readable default styling.

Manual review of the essay still found a composite or invented quotation and loose attribution. A quotation-matching warning was added to the application and applied to this saved result. This is a remaining semantic limitation, not a passed accuracy check. The original generation metrics and subsequent review are preserved in demo-results.json. A final small prompt adjustment requesting bold emphasis and experimental bullets has automated coverage through the general prompt tests but was not followed by another live essay generation.

A prior long generation lost its API response during a local database/API interruption. An exact-input, model- and session-isolated recovery cache now retains eligible completed generations for up to 24 hours. Cache isolation and expiry behavior are tested. The final services restarted successfully.

In total, the final source passed 33 automated checks (23 backend on PostgreSQL, 6 agent/cache, 4 frontend sanitizer) and the production build.

## Limits and remaining external work

- Citation validation checks that labels refer to supplied evidence. It does not prove entailment, correct attribution or numeric reasoning. Review outputs before presenting or publishing them.
- Cloud generation has not been exercised: no Anthropic API key was supplied. Missing-key behavior has been exercised.
- Docker Compose is supplied but has not been run on this Windows machine.
- Broad semantic accuracy, concurrent load, full keyboard/accessibility audit and 200% text scaling have not been established.
- The local workspace identifier separates sessions but is not production authentication.
- Public GitHub source is published at https://github.com/Sathvik257/lenny-growth-assistant; initial automated workflow run 34956514354 passed. The real camera-enabled YouTube demo and assignment form submission remain pending.

## Hosting and efficiency update

The expanded backend suite passed 29 tests on SQLite and separately on PostgreSQL; agent tests passed 6, frontend sanitizer tests passed 4, and the production build passed (39 automated checks in total). The PostgreSQL service was initially offline; it was restored and the full integration suite then passed. Dependency deprecation/configuration warnings remain in the saved log.

Added optional production reviewer authentication, secret validation, a single-generation gate, and a rolling global attempt limit. Database and agent URL normalization and pinned corpus downloads remain supported. Hosting-provider deployment files have been removed; the handoff targets reproducible local startup. Reviewer access is for a single-instance demo, not multi-user account authentication.

Retrieval precomputes guest names and promotional/introduction flags once instead of repeating regular expressions over the entire corpus on each question. Initialization is serialized to prevent duplicate index builds. HTML preview sanitization is memoized by artifact content and format, avoiding repeated parsing during typing/timers. No percentage speedup or model-generation acceleration is claimed.

Browser verification confirmed the updated layout and unavailable-provider notice. The latest source retains the previously recorded generation-quality limitations. The local Compose workflow has not been executed on the development machine; successful cloud model generation remains unverified without an API key.

## Final review — 14 September 2026

- 30 backend tests passed on PostgreSQL and SQLite, 6 agent tests passed, 4 frontend sanitizer tests passed: 40 automated checks. Production frontend build passed. Production dependency audit found 0 known vulnerabilities.
- Live smoke checks passed for database/corpus readiness (303 transcripts, 23,178 chunks), local-model availability, unsupported-query handling, missing-cloud-key errors, failed-turn rollback and temporary conversation cleanup. See live-checks.json.
- Browser reopened the latest completed user question and its evidence. The actual model generation took 136,688 ms. Manual review found Sean Ellis incorrectly associated with a Rahul Vohra source. Added an explicit bracketed guest/citation mismatch warning, including when displaying saved answers; its regression test passes. The answer remains a draft needing review. This detector is narrow and cannot establish semantic truth.
- Cloud generation remains unverified without an Anthropic key. The local Compose workflow remains unexecuted on this machine. Local writing remains slow and can misattribute evidence.

## Evidence fallback update

Added a deterministic transcript-excerpt fallback for detected explicit guest/source mismatches in newly generated Q&A. Two new tests verify persistence, no additional model call, and safe source markup handling. All frontend source files were hash-compared and are unchanged. This narrow safeguard does not establish semantic correctness for all answers. See docs/evaluator-guide.md for a concise review path.

The expanded backend suite passed 32 tests on SQLite and PostgreSQL. The unchanged agent and frontend suites previously passed 6 and 4 tests respectively (42 checks across the current suites).
