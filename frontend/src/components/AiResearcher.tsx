import { useId, useState } from 'react'

type Props = { ticker: string; name: string }

function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      <path
        d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.2 3.6A.5.5 0 0 1 5 19.2V16a2.5 2.5 0 0 1-1-2z"
        fill="currentColor"
      />
    </svg>
  )
}

// Placeholder until a research service exists: a chat window that names the company and says so
export default function AiResearcher({ ticker, name }: Props) {
  const [open, setOpen] = useState(false)
  const panelId = useId()

  return (
    <div className="ai-researcher">
      <button type="button" className="ai-researcher-toggle" aria-expanded={open} aria-controls={panelId} onClick={() => setOpen((o) => !o)}>
        <ChatIcon />
        AI Researcher
      </button>
      {open && (
        <div id={panelId} className="chat-window">
          <div className="chat-header">
            <span className="chat-avatar" aria-hidden="true">AI</span>
            <span>
              <strong>AI Researcher</strong>
              <span className="chat-presence">Offline</span>
            </span>
            <button type="button" className="chat-close" aria-label="Close AI Researcher" onClick={() => setOpen(false)}>
              <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </button>
          </div>
          <div className="chat-messages" role="status">
            <p className="chat-bubble">
              You've selected <strong>{name}</strong> ({ticker}) to research.
            </p>
            <p className="chat-bubble">Service Not Available</p>
          </div>
          <input className="chat-input" type="text" placeholder="Message AI Researcher…" aria-label="Message" disabled />
        </div>
      )}
    </div>
  )
}
