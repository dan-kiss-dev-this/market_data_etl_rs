# Shorter chat window

Status: ready-for-agent

The AI Researcher chat window is too tall. `.chat-window` has no height of its own; it is sized by its header, `.chat-messages` and `.chat-form`. Only `.chat-messages` is capped, at `max-height: min(60vh, 520px)`.

Halve that cap to `min(30vh, 260px)` in `frontend/src/index.css`. The message area halves on every screen size; the header and form keep their size, so the window as a whole ends up a little over half as tall.

## Acceptance

- With a full Blurb, the message area is at most 30vh / 260px tall and scrolls inside the panel
- Works at phone width
