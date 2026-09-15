# Deploy the research studio on Render

This repository includes a Render Blueprint for a password-protected review/demo website. It creates paid services; inspect the displayed cost before confirming. It is not a public multi-tenant SaaS deployment.

## Publish

1. Create your public GitHub repository and push this source, following publishing.md. Never commit .env or .runtime.
2. In Render, choose New > Blueprint and connect that repository. Render reads render.yaml.
3. Enter ANTHROPIC_API_KEY when requested. The same key and model setting are securely referenced by the API service. Review the service plans and displayed cost before creating resources.
4. The image downloads the transcript corpus at a pinned revision. The pre-deploy command imports it idempotently into PostgreSQL. This can make the first build/deploy take several minutes. A failed download or import fails deployment instead of silently creating an empty corpus.
5. After deployment, open lenny-studio's HTTPS URL. The browser asks for a username and password. Use reviewer and the generated ACCESS_PASSWORD from that service's environment settings. Share those credentials privately with your evaluator, never in the public repository.
6. Open Workspace settings and verify Anthropic, agent, and transcripts are ready. Run a short question, open its evidence, then create an essay and HTML brief. Reload and check that history persists. Check /api/health/ready using the same credentials.

## Deployment behavior

The web service serves React and FastAPI from one origin. The Pi agent has a private address and a generated service token. PostgreSQL external IP access is disabled. Render supplies HTTPS. The Python configuration normalizes Render's PostgreSQL connection URL and agent host:port automatically.

One API process and one agent handle one generation at a time. Concurrent requests receive a retryable 429 rather than consuming database connections and model work. A global rolling limit permits 30 generation attempts/hour; it is a demo guard, not a billing guarantee. It resets on restart and is not distributed. Do not add replicas/workers without replacing it with a shared limiter and job queue. Set a provider-side spending limit too.

Hosted generation has a 240-second model deadline; a larger essay may time out and should be retried or shortened. This synchronous demo does not promise durable in-flight work across deployments. Completed conversations and artifacts live in PostgreSQL. Agent recovery cache is ephemeral and may disappear on redeploy.

Ollama is intentionally not provisioned in this Blueprint. Keep the local installation for the mandatory Ollama camera demo. Selecting Ollama on the hosted site shows a connection notice and disables sending until a model is configured.

## Validation status

The Blueprint and deployment helpers are checked locally. An actual Render build, cloud generation, and HTTPS authentication smoke test still require your repository, Render account and Anthropic key. No successful cloud deployment is claimed. Docker is unavailable on the development machine, so image execution is also unverified.

References: https://render.com/docs/blueprint-spec and https://render.com/docs/health-checks.
