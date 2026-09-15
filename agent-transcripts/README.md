# Development record

Final publication pass, 15 September 2026: fixed omitted artifact content in follow-ups, remapped old citation labels, added malformed-response validation, and made startup identify this workspace before reusing a port. Installed Python/Node dependencies in a separate source copy; 37 backend, 9 agent/startup and 4 sanitizer tests passed, plus production build. Downloaded/imported three real transcripts into a new database and verified API persistence across clients. PostgreSQL initially needed restarting. Added GitHub Actions; source destination supplied by user is Sathvik257/lenny-growth-assistant. No cloud-generation, video, or form-completion claim is made.

This folder contains a sanitized engineering record from the AI-assisted build. It includes actual commands, observed failures and corrections. It is a curated log, not a fabricated verbatim export or hidden model reasoning. Add the platform's full conversation export here if the evaluator requires the complete original coding-agent transcript.

No API keys, private account data, raw environment files or model downloads belong in this folder.

## Recorded work

1. Read the supplied assignment. Extracted required FastAPI, PostgreSQL, Pi/Claude agent SDK, Ollama demo, grounded answers, essay skill, artifact viewer, security, tests and handoff requirements.
2. Checked the empty workspace and installed dependencies. Docker and Ollama were absent. Read Pi SDK docs and the linked Ship 30 guide.
3. Wrote PRD before implementation. Chose a local research studio, bounded lexical retrieval, explicit provider switching and no autonomous shell tools.
4. Built FastAPI persistence, ingestion, retrieval and React interface; downloaded the actual 303-file corpus at revision be8ab89a890a833cbba2c892178f823fff178c65.
5. Found a deprecated Pi package with security advisories. Replaced @mariozechner/pi-coding-agent 0.73.1 with @earendil-works/pi-coding-agent 0.85.1 and adapted the SDK integration. npm audit then reported zero vulnerabilities.
6. Portable PostgreSQL initially used Windows CP1252. Ingestion failed on Unicode. Created an explicitly UTF-8 database and fixed portable initialization to use UTF-8. Ingestion completed with 303 transcripts and 23,178 chunks.
7. Initial unit tests exposed a BM25 edge case on a two-document corpus: IDF could be zero, producing false empty retrieval. Added positive IDF smoothing. All 19 backend tests passed on SQLite and separately on PostgreSQL.
8. The initial Vite build encountered a sandbox filesystem restriction. Running the build with the reviewed execution permission succeeded.
9. Live Ollama returned uncited answers. The application rejected them rather than persisting invalid citations. Reworked the output contract, added one bounded repair, and reduced sampling temperature.
10. Found the maintained Pi agent property is streamFunction, not streamFn. Corrected the integration so sampling settings actually apply.
11. Inspected the desktop UI; adjusted contrast, compact-screen layout, local font bundling and artifact panel width.

See docs/verification.md for the final validation status and remaining checks.

12. A final test invocation hit Windows temporary-directory ownership restrictions. Re-ran with a fresh project-owned temporary directory successfully, then configured future tests to use unique temporary directories under .runtime.
13. A real qwen2.5:3b response supplied valid citations but inverted a percentage and cited an introductory passage. This was a semantic failure, not a successful grounding check. Tightened evidence instructions and changed retrieval to score body text, reduce speaker-name dominance and downweight introductions. Semantic correctness still requires review.
14. Switched the default local model from 1.5B to 3B and raised the generation timeout to 15 minutes for the available CPU. No cloud fallback was used.
15. Built a hostile-HTML browser fixture using the production sanitizer: safe content remained visible and the script probe did not execute. DOMPurify tests also cover hostile tags, handlers and CSP insertion.

16. The 912-word essay also invented a book title from episode metadata. Removed episode titles from model evidence headers.
17. A first section-based approach collapsed to bare headings after several turns. Replaced accumulated drafting history with a fresh isolated Pi session per section, sharing only original evidence and an outline; added a regression test that rejects incomplete sections.
18. Restricted explicitly named guest queries to the requested guest to avoid borrowing unrelated speakers' advice. Added an attribution-boundary regression test.
19. Added conservative paragraph editing for overlong drafts and tested preservation of section leads, lists, sentence boundaries and the takeaway. Raised the overall CPU timeout to 25 minutes.
20. Reopened a saved artifact in a new browser tab, toggled source view, and verified the downloaded Markdown file appeared in Downloads. The browser automation download event timed out even though the file was saved. Clipboard write showed UI feedback, but the automation clipboard read did not confirm its contents.

21. A local database/API interruption lost an in-flight response. Added a bounded, exact-input recovery cache isolated by session and model, with expiry and malformed-entry tests.
22. Removed promotional retrieval passages and cleaned echoed section scaffolding after live failures exposed both. Added a quotation-matching warning; valid citation labels alone remain insufficient to establish semantic accuracy.
23. Final local outputs measured 1,360 essay words in 391 seconds and 106 HTML words in 80 seconds. The essay still needed attribution/quotation review; applied the new warning to its saved message. Inspected the final HTML artifact in the browser.
24. Final verification passed 23 PostgreSQL backend tests, 6 agent/cache tests, 4 frontend sanitizer tests, and the production build. npm audit reported zero vulnerabilities. Cloud generation and Docker execution remain unverified.
25. The user will create the public repository later. Prepared a source-only archive and publishing/demo instructions; no repository, video or form submission was fabricated.

26. Prepared Render Blueprint, production secret validation, reviewer Basic authentication, single-request generation gate and hourly limit. Precomputed retrieval flags and memoized HTML sanitization. Improved connection guidance, readability, focus and reduced-motion behavior. Expanded tests passed; restored the stopped local database before PostgreSQL integration validation. Cloud/Docker execution remain pending.

27. Final 14 September review reran the production build, production audit, 30 backend tests on PostgreSQL/SQLite, 6 agent tests and 4 sanitizer tests. Live infrastructure smoke checks passed. Browser review exposed a guest/source mismatch in the latest saved answer; added a narrow warning and regression coverage without rewriting the original answer. Cloud and Docker verification still require external prerequisites.

28. Preserved every frontend source file unchanged (SHA-256 comparison). Added transcript-excerpt fallback for explicit guest/source mismatch in new Q&A, plus regression tests. Added evaluator guide explaining the evidence-first design and honest limitations.
