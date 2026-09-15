# Lenny Growth Assistant

A local research studio that turns Lenny's Podcast transcripts into cited answers, Ship 30 essays and rendered Markdown/HTML artifacts.

React + TypeScript frontend · FastAPI · PostgreSQL · Pi Coding Agent · Ollama / Anthropic

## Start here

On the prepared Windows workspace, run:

```powershell
.\start.ps1
```

Open the URL printed by startup (normally **http://127.0.0.1:8000**). The launcher skips ports occupied by other projects and writes the selected URL to `.runtime/preview-url.txt`. Use `.\start.ps1 -Port 8001` to prefer port 8001. The script builds the frontend, starts project-local services, downloads the model/corpus if needed, and imports changed transcripts. Node 24 and Python 3.12 are prerequisites for a fresh native setup. Runtime data stays in ignored .runtime/ and data/transcripts/.

For an evaluator with Docker and Docker Compose installed:

```sh
cp .env.example .env
docker compose up --build -d
```

The initial run downloads a local model and the upstream transcripts. Watch progress with `docker compose logs -f model-init ingest`. Once initialized, open http://127.0.0.1:8000. Only the app port is published, bound to loopback. On Windows, use `Copy-Item .env.example .env` instead of cp.

Docker configuration is supplied for reproducibility; see docs/verification.md for what was actually exercised on the development machine.

## What to try

- “How does Sean Ellis measure product market fit with a survey?”
- “How does Teresa Torres recommend doing continuous product discovery?”
- In the same conversation: “Turn that into an essay for a product manager.”
- Select Create an artifact: “Create a one-page HTML brief from that discussion.”
- Ask an unrelated question to see the evidence limitation.

Click a source label to inspect its passage. The artifact tab supports preview, source inspection, copy, download and earlier artifact selection. Chats and artifacts persist in PostgreSQL. A new conversation starts independent context.

## Native development

Prerequisites: Node.js 24, Python 3.12, PostgreSQL 17+ with UTF-8 encoding, and Ollama. A 16 GB machine can run the default 3B model, but leave several GB of free memory and expect CPU latency. CPU-only answers can take several minutes; long essays may take 10–25 minutes. Configure a larger model only if your hardware supports it.

```sh
python -m venv .venv
# Activate .venv with your shell's activation command.
pip install -r requirements.txt
npm ci --ignore-scripts
cp .env.example .env
```

Set DATABASE_URL for your PostgreSQL instance. The optional `npm run db:local` uses a portable PostgreSQL server on 127.0.0.1:54329 with local-only defaults. The Windows startup script uses this automatically.

```sh
ollama serve
# In another terminal:
ollama pull qwen2.5:3b
python scripts/fetch-transcripts.py
python -m backend.ingest
npm run build
```

Start the agent and API in separate terminals:

```sh
npm run agent
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

For frontend development, `npm run dev` serves Vite on port 5173 and proxies /api to FastAPI. Production uses the built frontend served by FastAPI, so no separate web server is needed.

## Configuration

| Variable | Default / role |
|---|---|
| DATABASE_URL | PostgreSQL URL; required, see .env.example |
| LLM_PROVIDER | ollama |
| APP_PORT | 8000; preferred native preview port, with conflict detection |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 |
| OLLAMA_MODEL | qwen2.5:3b |
| ANTHROPIC_API_KEY | Optional, enables cloud generation |
| ANTHROPIC_MODEL | claude-sonnet-4-5 |
| AGENT_URL | http://127.0.0.1:8788 |
| AGENT_TOKEN | Shared private-service credential; change before non-local use |
| MODEL_TIMEOUT_SECONDS | 1500 (25 minutes), covering the complete generation |
| TRANSCRIPT_DIR | data/transcripts/episodes |
| RETRIEVAL_LIMIT | 5 |
| ALLOW_SQLITE | false; true only in unit tests |
| ENVIRONMENT | development; production enforces secret checks |
| ACCESS_USERNAME | reviewer; hosted demo login name |
| ACCESS_PASSWORD | Empty locally; at least 16 characters in production |
| GENERATION_REQUESTS_PER_HOUR | 30; single-process generation attempt limit |

Restart the API and agent after editing configuration. Download a new Ollama model before changing OLLAMA_MODEL. Selecting a provider in the UI does not edit server credentials. Cloud generation sends the question, bounded conversation history and relevant passages to Anthropic. Local mode never automatically falls back to cloud.

## Tests and evaluation

```sh
python -m pytest -q
npm run test:agent
npm run test:ui
npm run build
python -m scripts.evaluate-retrieval
```

Unit tests use an isolated temporary SQLite database, never the application database. To run the same persistence tests against PostgreSQL, create a dedicated UTF-8 database whose name ends in _test, then set TEST_DATABASE_URL before pytest.

PowerShell example:

```powershell
$env:TEST_DATABASE_URL='postgresql+psycopg://lenny:lenny_local_only@127.0.0.1:54329/lenny_test'
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:TEST_DATABASE_URL
```

The test suite covers ownership isolation, independent chats, persistence, deletion, invalid inputs, missing/unknown citations, model failure rollback, unsupported questions, ingestion refresh and routing. See docs/manual-test-plan.md for browser and semantic answer review. Retrieval results are in docs/retrieval-results.json and are limited to the stated test set.

## Knowledge refresh

`python scripts/fetch-transcripts.py` records the upstream Git revision and downloads actual files. `--limit 20` is available for a small first run. `python -m backend.ingest` updates changed files transactionally using SHA-256 hashes. Restart the API after refreshing to rebuild its in-memory retrieval index.

The source repository contains metadata inconsistencies; citations are evidence pointers, not an assurance that all upstream metadata is correct. Check the actual speaker and passage. See architecture.md for retrieval and grounding limits.

The source corpus is downloaded, not committed. Source: https://github.com/ChatPRD/lennys-podcast-transcripts. Writing principles: https://www.ship30for30.com/post/how-to-start-writing-online-the-ship-30-for-30-ultimate-guide. Respect the original creators' rights when publishing generated material.

## Troubleshooting

| Symptom | Action |
|---|---|
| Ollama not configured | Start Ollama and pull the exact configured model; refresh workspace status |
| Missing cloud key | Set ANTHROPIC_API_KEY in .env and restart both services |
| Model busy | Wait for the active generation; local concurrency is deliberately one |
| Model timeout | Close memory-heavy apps, use a smaller model, or increase the timeout |
| Citation check failed | Retry or choose a stronger model; rejected output is not saved |
| Essay length warning | Review/revise the draft before publishing; the app does not hide deviations |
| Database unavailable | Check DATABASE_URL and PostgreSQL; use UTF-8 encoding |
| Empty knowledge base | Fetch transcripts, run ingestion, restart API |
| Address in use | Native startup selects a free port; use its printed URL or set APP_PORT. Do not assume another app at port 8000 is this project |
| Startup looks slow | First model download and model load take time; inspect .runtime logs or Compose logs |

GET /api/health/live checks the process; GET /api/health/ready checks database and corpus readiness. GET /api/status also checks agent and configured Ollama model availability. Interactive API docs are at /docs. Request IDs are returned on responses. Runtime logs deliberately omit prompts, source excerpts and credentials.

Compose stop: `docker compose down` preserves named volumes. Do not add -v unless you intend to erase all local chats, corpus and model downloads. For native development, stop foreground terminals normally; the Windows launcher runs services in the background. See .runtime/services.json for the processes it started.

## Project map

- src/: interface, Markdown rendering and HTML sandbox preparation
- backend/: FastAPI, PostgreSQL models, ingestion, retrieval and generation boundary
- agent/: Pi SDK service and prompt assembly
- skills/ship-30/SKILL.md: versioned writing skill
- scripts/: corpus download, local launch and retrieval evaluation
- tests/: backend behavior tests
- agent-transcripts/: sanitized development record, including failures and corrections
- PRD.md, design.md, architecture.md: product and engineering handoff
- docs/demo-script.md: camera demo plan

## Submission

Publish the source as a public GitHub repository, record the real 2–3 minute camera-enabled demo and upload it to YouTube, then submit both links through the assignment form. No repository URL or video URL is fabricated in this package. The recorded deadline is 15 September 2026 EOD; the brief does not specify a timezone.

This is a local evaluation product. Production exposure requires real authentication, authorization, TLS, rate limits and operational hardening. Browser workspace IDs are not authentication.

## Host on Render

Use the included `render.yaml` Blueprint and follow [the deployment guide](docs/render-deployment.md). It creates a free web service with an internal Pi agent and free PostgreSQL. Leave Root Directory blank. The hosted demo uses 40 real transcripts to fit 512 MB RAM; the native version keeps the full corpus. Free hosting does not include free AI: add an existing Anthropic key separately to enable generation. Without a model connection the website opens but generation is unavailable. Free PostgreSQL expires after 30 days. Keep Ollama on your computer for the assignment demo.

## Assignment checklist

See [docs/assignment-audit.md](docs/assignment-audit.md) for evidence against every requirement and the remaining submission steps. Public hosting is optional in the supplied brief; local Ollama demonstration, public source repository and camera-enabled YouTube video are required.

## Repository and verification

Submission repository: https://github.com/Sathvik257/lenny-growth-assistant.

The GitHub Actions workflow runs PostgreSQL API tests, agent/startup tests, sanitizer tests and the production build on pushes and pull requests. Check the Actions tab for the result for your exact commit. Local verification and its limits are recorded in docs/verification.md. The orange frontend was preserved throughout the final backend and startup fixes.
