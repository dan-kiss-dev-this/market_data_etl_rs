# 02: Chat UI in the AI Researcher panel

**What to build:** `frontend/src/components/ChatWithAI.tsx`, which replaces the disabled input in `AiResearcher.tsx` with a working, streamed chat. See `../spec.md`.

**Blocked by:** 01

**Status:** ready-for-agent

- [x] `api.chatAllowance()` and `api.chat(ticker, messages, onText)`, which reads the response body stream. `chatAllowanceQuery` in `queries.ts`
- [x] A form with the input and a Send button. The message log uses `role="log"`, apart from the Blurb's `role="status"` region
- [x] Over 250 chars: an alert (`role="alert"`) says "Messages can be up to 250 characters. You're N over." and Send is disabled
- [x] Send is also disabled when the draft is empty, while a reply streams, and when no messages are left
- [x] Shows "N of 5 messages left today"
- [x] Without a current Blurb, the input is disabled with "Chat only works for Leaders, the top 50 companies by RS rating."
- [x] 429 messages: "You've used your 5 messages for today." and "The AI Researcher is busy today. Try again tomorrow."
- [x] The conversation resets when the ticker changes
- [ ] Styles next to the existing `.chat-*` rules: user bubbles, the counter, the alert and the button, in light and dark themes and at phone width
- [x] `ChatWithAI.test.tsx` covers the alert and disabled Send, non-Leaders disabled, a streamed reply, the 429 messages and the remaining count
- [x] `npm test` and `npm run build` pass

## Comments

- `ChatWithAI` takes the Blurb as `children` so the Blurb and the conversation share one scroll area. The Blurb keeps `role="status"` and the conversation is a separate `role="log"`.
- The allowance query is refetched after every send instead of being read from `X-Chat-Remaining`, so the reason (visitor or site) is always current.
- Open: checking it in the browser in light and dark themes and at phone width.
