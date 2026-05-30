---
name: commit
description: Use when the user asks to commit changes, make a commit, commit staged changes, or commit the current work. Enforces conventional commits and careful staging.
---

# Commit Changes

Use this skill when the user asks to commit changes.

## Workflow

1. Inspect repository state before committing:
   - `git status --short`
   - `git diff`
   - `git diff --cached`
   - `git log --oneline -10`

2. Determine the commit scope:
   - If the user says to commit staged changes, commit only what is already staged.
   - If the user asks to commit all current work, stage only files that are clearly part of the requested work.
   - Do not stage unrelated user changes.
   - If staged changes include unrelated work, ask before changing the staging area.

3. Verify when appropriate:
   - Run the narrowest relevant test/build command for the changed files.
   - If verification is skipped, say why in the final response.

4. Use a conventional commit message:
   - `feat: ...` for user-visible features or new behavior.
   - `fix: ...` for bug fixes.
   - `test: ...` for test-only changes.
   - `docs: ...` for documentation-only changes.
   - `refactor: ...` for restructuring without behavior change.
   - `chore: ...` for tooling, dependency, or maintenance work.
   - Keep the subject concise, imperative, and lowercase after the type.

5. Commit non-interactively:
   - `git add <specific files>` when staging is needed.
   - `git commit -m "type: concise subject"`

6. After committing:
   - Run `git status --short`.
   - Report the commit hash, message, verification run, and any remaining uncommitted files.

## Rules

- Never use `git add .` unless every changed file has been inspected and belongs in the commit.
- Never amend unless the user explicitly asks.
- Never use destructive commands like `git reset --hard` or `git checkout --` unless explicitly approved.
- Preserve unrelated user work.
- Prefer one meaningful commit over many tiny commits unless the user asks otherwise.
