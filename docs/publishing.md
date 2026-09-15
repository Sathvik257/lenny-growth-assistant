# Publish your finished source

Submission repository: https://github.com/Sathvik257/lenny-growth-assistant. The steps below also explain how to publish an extracted copy manually.

1. Extract **Lenny-Growth-Assistant-Source.zip** into a new folder. Publish that extracted source folder so runtime files and local testing utilities stay out of the repository.
2. On GitHub, create a **public**, empty repository. Leave README, license and .gitignore initialization unchecked because this project already has its source files.
3. Open a terminal in the extracted Lenny-Growth-Assistant folder. With Git installed, run:

```sh
git init
git add .
git status --short
git commit -m "Build Lenny Growth Assistant"
git branch -M main
git remote add origin https://github.com/Sathvik257/lenny-growth-assistant.git
git push -u origin main
```

Replace the remote URL with the URL of the repository you created. Review the staged list before committing: .env, .runtime, node_modules, .venv and downloaded transcript files should not appear. The supplied .env.example contains local demonstration defaults and an empty cloud key.

4. Open the public repository while signed out. Check that README, PRD, design, architecture, skill, tests and agent logs are visible. Follow the startup instructions from a fresh clone if possible.
5. Record and upload the actual camera-enabled video using demo-script.md. Check its link while signed out.
6. Submit both real links using https://forms.gle/LgotDHNVxW1mbzNE7.

The source ZIP and verification report are a handoff, not evidence that the repository or video has already been published.
