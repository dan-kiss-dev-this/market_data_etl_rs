# README: where the AI Researcher's news comes from

Status: ready-for-agent

The README doesn't say where the panel's news Sources come from. All news comes from the Blurb run. `massive.ticker_news` fetches the Leader's last 30 days of Massive news. Haiku cites up to 3 headlines by number in `catalyst_sources`, and `cited_headlines` saves those real headlines with the Blurb (`backend/app/blurbs.py`). The panel's Sources and the Chat with AI context (`backend/app/chat_with_ai.py`) both read the saved headlines. Chat makes no news call of its own and sees only the cited headlines, not all 30 days.

Add this to the README's "Blurb run" section, and mention the cited headlines in the "Chat with AI" section.

## Acceptance

- The README says the news comes from the Blurb run's last 30 days of Massive news
- It says Haiku only picks headlines by number and can't invent a source or a link
- It says chat uses only the cited headlines, so its news is only as fresh as the latest Blurb run
