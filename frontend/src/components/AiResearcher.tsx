import { useQuery } from '@tanstack/react-query'
import { useId, useState } from 'react'
import type { BlurbFields, MarketDirection } from '../api'
import { blurbQuery } from '../queries'

type Props = { ticker: string; name: string }

const FIELDS: [keyof BlurbFields, string][] = [
  ['what_they_sell', 'What they sell'],
  ['catalyst', 'Catalyst'],
  ['category_position', 'Category position'],
  ['momentum', 'Momentum'],
  ['risks', 'Risks'],
]

const MARKET_CLASS: Record<MarketDirection['status'], string> = {
  Uptrend: 'market-up',
  'Under pressure': 'market-pressure',
  Downtrend: 'market-down',
}

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

function MarketBadge({ market }: { market: MarketDirection }) {
  return (
    <p className={`market-badge ${MARKET_CLASS[market.status]}`}>
      S&amp;P 500: {market.status}
      {market.breadth !== null && (
        <span title="Share of S&P 500 companies above their own 50-day average">
          {' '}
          · Breadth {Math.round(market.breadth * 100)}%
        </span>
      )}
    </p>
  )
}

// Shows the selected company's latest Blurb, written by the weekly Blurb run; only Leaders have one
export default function AiResearcher({ ticker, name }: Props) {
  const [open, setOpen] = useState(false)
  const panelId = useId()
  const { data, isPending, isError } = useQuery({ ...blurbQuery(ticker), enabled: open })

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
              <span className="chat-presence">{data ? 'Online' : 'Offline'}</span>
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
            {isPending && <p className="chat-bubble">Looking up {name}…</p>}
            {isError && <p className="chat-bubble">Couldn't load the Blurb right now. Try again later.</p>}
            {data === null && <p className="chat-bubble">No current Blurb. Blurbs cover the top 50 by RS rating.</p>}
            {data && (
              <>
                {data.market && <MarketBadge market={data.market} />}
                {FIELDS.map(([key, label]) => (
                  <p key={key} className="chat-bubble">
                    <strong className="blurb-label">{label}</strong>
                    {data.blurb[key]}
                  </p>
                ))}
                <p className="blurb-meta">Updated {data.date}</p>
                {data.headlines.length > 0 && (
                  <ul className="blurb-sources" aria-label="Sources">
                    {data.headlines.map((h) => (
                      <li key={h.url}>
                        <a href={h.url} target="_blank" rel="noreferrer">
                          {h.title}
                        </a>{' '}
                        <span>
                          {h.publisher}, {h.date}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
          <input className="chat-input" type="text" placeholder="Message AI Researcher…" aria-label="Message" disabled />
        </div>
      )}
    </div>
  )
}
