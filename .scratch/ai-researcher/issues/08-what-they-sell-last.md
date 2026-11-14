# Panel: show What they sell last

Status: ready-for-agent

The AI Researcher panel shows the Blurb fields in the order What they sell, Catalyst, Category position, Momentum, Risks. Move What they sell to the end, after Risks, so the panel leads with the Catalyst. Only the panel's display order changes (`FIELDS` in `frontend/src/components/AiResearcher.tsx`); the Blurb model, the prompt and the Chat with AI context are unchanged.

## Acceptance

- [x] The panel shows Catalyst, Category position, Momentum, Risks, What they sell, in that order
- [x] A test in `AiResearcher.test.tsx` checks the order
- [x] Spec updated

## Comments

- vitest 44/44 passing, 2026-11-14; chat context order (`backend/app/chat_with_ai.py`) left unchanged.
