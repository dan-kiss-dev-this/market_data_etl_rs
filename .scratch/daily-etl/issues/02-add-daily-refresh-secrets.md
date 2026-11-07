# 02: Add the daily refresh secrets to GitHub

**What to build:** The repo's GitHub Actions secrets contain the two values the daily refresh needs, so a scheduled run can reach Supabase and Massive. Add them under the repo's Settings → Secrets and variables → Actions, or with `gh secret set <NAME>`, which prompts for the value:
- `DATABASE_URL`: the Supabase session-pooler URL, the same one Render uses (see ADR 0001 for why it must be the pooler host)
- `MASSIVE_API_KEY`: the Massive API key

The owner enters the values. An agent must not read, print or copy `backend/.env`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [ ] `gh secret list` shows `DATABASE_URL` and `MASSIVE_API_KEY`
- [ ] No secret values appear in the repo, commits or chat
