# Your Lenny Growth Assistant

The assignment asks for a working AI application plus an engineering handoff. This project implements that application with a custom research-studio interface, real podcast retrieval, a Pi agent, PostgreSQL history, an Ollama/cloud switch, a reusable essay skill, and a sandboxed artifact viewer.

## Run your prepared copy

1. Open PowerShell in this folder and run `./start.ps1`.
2. Open http://127.0.0.1:8000.
3. Keep Ollama selected for the required local-model demonstration. Model generation on this CPU can take several minutes; prepare the essay and HTML document before recording.

Start with README.md. Review docs/verification.md for measured results and remaining limitations. PRD.md, design.md and architecture.md explain the implementation. The files in agent-transcripts/ preserve development failures and actual test logs.

## Finish the external submission

- Read and understand the code and trade-offs so you can explain your own submission.
- Publish the source package to a public GitHub repository using docs/publishing.md. Keep .env, .runtime, dependencies and downloaded transcripts excluded.
- Record a real 2–3 minute demo with your camera visible, following docs/demo-script.md. Show the running local model, evidence, saved chats, essay and artifact. Upload it to YouTube and check access to the link.
- Submit the repository and video links using the assignment form: https://forms.gle/LgotDHNVxW1mbzNE7.

The brief lists 15 September 2026 EOD as its deadline and does not specify a timezone. No public repository, video upload or form submission has been performed by this project.

## Host on Render

Use the included `render.yaml` Blueprint and follow [the deployment guide](docs/render-deployment.md). It provisions a password-protected hosted demo with a private Pi agent and PostgreSQL. Paid Render services and an Anthropic API key are required; keep Ollama on your computer for the assignment demo. Cloud deployment still needs a live smoke test.

For the current orange local preview use http://127.0.0.1:8001/ while another project occupies port 8000. The source archive retains the original orange interface. Read docs/evaluator-guide.md for the review walkthrough and engineering trade-offs.
