# Deploy the research studio on Render

This repository includes a free Render Blueprint for the backend and a Vercel proxy for the frontend. The hosted demo is not a public multi-tenant SaaS deployment. Free hosting does not provide a free AI model.

## Publish

1. In Render, choose New > Blueprint, connect this repository, select `main`, and leave Root Directory blank. Render reads `render.yaml` from the repository root.
2. Confirm that the plan shows one Free web service and one Free PostgreSQL database, then apply it. No payment is required for these resources.
3. Wait for `lenny-studio-free` to deploy. Its startup imports 40 pinned real transcripts and starts FastAPI plus the loopback-only Pi agent in one container.
4. Copy the service's `https://...onrender.com` URL and its generated `ACCESS_PASSWORD` value.
5. In Vercel project settings, add `BACKEND_URL` with the Render URL and `BACKEND_ACCESS_PASSWORD` with that generated password. Apply them to Production, then redeploy the latest GitHub commit. Keep Vercel Root Directory blank and enable Fluid Compute so the proxy can wait up to 300 seconds for long generation calls. Do not use a `VITE_` prefix for the password: it must remain server-side.
6. Open the Vercel URL. Workspace status should show the database, agent and transcripts ready. Anthropic remains Not configured until you add `ANTHROPIC_API_KEY` manually under the Render service's Environment settings and redeploy.

## Deployment behavior

The Vercel frontend calls its same-origin `/api` proxy. That server-side proxy forwards requests to Render and adds the generated reviewer credential without exposing it to browser JavaScript. Render runs FastAPI and the Pi agent in one free container; the agent listens only on loopback. PostgreSQL external IP access is disabled. Render and Vercel supply HTTPS.

One API process and one agent handle one generation at a time. Concurrent requests receive a retryable 429 rather than consuming database connections and model work. A global rolling limit permits 30 generation attempts/hour; it is a demo guard, not a billing guarantee. It resets on restart and is not distributed. Do not add replicas/workers without replacing it with a shared limiter and job queue. Set a provider-side spending limit too.

Hosted generation has a 240-second model deadline; a larger essay may time out and should be retried or shortened. This synchronous demo does not promise durable in-flight work across deployments. Completed conversations and artifacts live in PostgreSQL. Agent recovery cache is ephemeral and may disappear on redeploy.

Ollama is not provisioned because its model cannot fit Render's 512 MB free instance. Keep the local installation for the mandatory Ollama camera demo. The free hosted site works for browsing the application and stored sessions, but AI generation needs a separately configured model connection. Anthropic usage can incur API charges.

## Validation status

GitHub Actions builds the exact free container, runs it with a 512 MB memory cap, and checks the frontend, database, agent, real transcript retrieval, persistence and cleanup. Render's free service sleeps after 15 idle minutes and can take about a minute to wake. Free PostgreSQL expires after 30 days. A successful live Render/Vercel deployment and cloud generation still require external configuration; no successful cloud deployment is claimed until those checks are run.

References: https://render.com/docs/blueprint-spec and https://render.com/docs/health-checks.
