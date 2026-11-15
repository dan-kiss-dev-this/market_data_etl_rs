## Agent skills

### Issue tracker

Issues are local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

Whenever you plan a change (including in plan mode), also write it as a ticket at `.scratch/<feature>/issues/NN-<slug>.md` following `docs/agents/issue-tracker.md`, without being asked.

### Triage labels

The five default triage roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), recorded as `Status:` lines in the issue files. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### Tests first

Any code added or changed gets a test (pytest for `backend/`, Vitest for `frontend/`). Write the test first and run it to see it fail, then write the code to make it pass. Tickets list the test as their first checkbox.
