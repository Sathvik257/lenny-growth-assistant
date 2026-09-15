# Manual UI test plan

1. Open a fresh browser workspace. Confirm corpus count and provider status reflect actual services. New conversations should be empty.
2. Use a starter. Confirm it fills the composer and remains editable. Send a supported question; check the loading state, response, citations and evidence passages.
3. Ask a referential follow-up. Verify the answer stays on the previous topic. Open another conversation; verify messages do not leak between them.
4. Reload the page and reopen a saved conversation. Check messages and artifacts persist.
5. Ask an unrelated unsupported question. Confirm a limitation without invented citations.
6. Generate an essay. Check 1,100–1,400 words, clear hook, useful sections, inline citations and a concrete final action. Review each substantive claim against its passage.
7. Generate Markdown and HTML artifacts. Verify side-by-side preview, source view, copy, download and persisted artifact selection.
8. Stop Ollama. Send a request; confirm a useful error and preserved draft. Restore Ollama and retry.
9. Select cloud without a key. Confirm a clear missing-key error. Configure a real key in .env, restart, and manually validate cloud generation.
10. Stop PostgreSQL. Verify a structured service error. Restore it; refresh service status and confirm saved chats remain.
11. Check mobile width, keyboard navigation, Escape closing dialogs, visible focus, 200% text scaling and reduced motion.
12. Render hostile HTML with script, img onerror, iframe, form, CSS url and meta refresh. Confirm no script or network access, no parent DOM mutation and readable safe content.

The browser workspace identifier is not production authentication. Do not expose this deployment publicly as an authenticated service.
