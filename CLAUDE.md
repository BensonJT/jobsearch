# Jobsearch — Claude Working Agreement

## Active Memory Files (loaded at session start)
@/docs/STATUS.md

## North Star (do not optimize away)
Jobsearch simplifies and automates the process of finding and applying for jobs,
leveraging intelligent search and application tracking to help the user manage
their career growth efficiently.

## Current Scope
- Initializing the project structure.
- Setting up a Python-based application environment.
- Planning the core features: job scraping/searching, application tracking, and resume tailoring.

## Repo map (where to look first)
- Backend: `backend/` (To be created)
- Frontend: `frontend/` (To be created)
- Docs source of truth: `docs/`

## Local environment
Xubuntu Linux (optiplex) · conda env `jobsearch` · Python 3.12+

## Session continuity (STATUS.md)
`docs/STATUS.md` is the session state file — read it first, update it last.
- **Start:** Output the SESSION START CONFIRMATION block before doing anything else
- **End:** Overwrite STATUS.md with current state snapshot (git history is the changelog)
- Do not wait to be asked — updating STATUS.md is part of wrapping up, same as a commit
- Keep it concise — bullet points preferred over prose

## Sprint Plan (when active)
If `docs/SPRINT_PLAN.md` exists, it is a binding contract.
- Execute tasks in checklist order — do not reorder without explicit user confirmation
- Write the finalized plan to `docs/SPRINT_PLAN.md` using the established structure
- Restore `@/docs/SPRINT_PLAN.md` in the Active Sprint section of `docs/STATUS.md`

## When uncertain
- Ask a single focused question, then proceed with a reasonable default.

## Coding standards
- Python: follow PEP 8; use type hints where practical; keep functions readable; 
  add concise comments/docstrings.
- Prefer "boring, maintainable" implementations over novel ones.

## Git commits:
- After completing any meaningful unit of work, commit locally with a
  descriptive commit message.
- Commit message format:
  - First line: short summary in imperative mood, max 72 chars
  - Blank line
  - Body: 2–5 bullets explaining what changed and why
- Group related changes into one commit.
- Do NOT push to GitHub — the user handles all pushes.
