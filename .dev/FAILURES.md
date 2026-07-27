# Failures

## 2026-07-27: `git add <deleted-path>` aborted staging; deletion swept into wrong commit

- **What happened:** `base.py` was removed with `git rm` (staging the deletion), then later commits staged specific files with `git add fileA fileB ...`. When one `git add` included the already-deleted `base.py` path, the whole `git add` aborted with a pathspec error — but the previously-staged deletion stayed in the index and got committed with the *cardinality* fix instead of the intended tidiness commit.
- **Why it matters:** Broke one-concern-per-commit; the dead-file removal is now mixed into a bug-fix commit.
- **Fix / avoidance:** Stage a deletion in the same `git add` group as its intended commit, and run `git status` between commits to see what's actually staged before committing. Don't reference an already-deleted path in a later `git add`.
- **Tags:** git, workflow

## 2026-07-27: CI silently red for ~2 weeks because releases don't gate on it

- **What happened:** `pip-audit` in `ci.yml` had failed on every `main` push since v2.3.1 (2026-07-15) — the runner's `setuptools 79.0.1` is flagged by PYSEC-2026-3447. It went unnoticed because `publish.yml` (tag-triggered) doesn't run pip-audit, so v2.3.2 published green while CI was red.
- **Why it matters:** A red CI that doesn't block releases trains you to ignore CI. setuptools here is a build-env tool, not a datascope runtime dep, so the package was fine — but the next red could be real.
- **Fix / avoidance:** Fixed by upgrading setuptools in the CI install step. Check `gh run list --workflow=ci.yml` after pushes; consider having the publish workflow depend on CI passing.
- **Tags:** ci, release, dependencies
