# Git workflow

All changes — code or docs beyond a trivial one-line fix — go through a feature branch and a pull request. Never commit directly to `main`.

1. `git checkout -b feature/<short-name>` before making changes.
2. Commit on that branch.
3. `git push -u origin feature/<short-name>`
4. `gh pr create` with a clear description of what changed and why.
5. Stop there — don't merge automatically. Merging to `main` triggers a live redeploy (Railway/Vercel), so that's the user's call unless they've explicitly said to merge.
