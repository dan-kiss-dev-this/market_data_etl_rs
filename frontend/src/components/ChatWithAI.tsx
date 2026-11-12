import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useId, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { api, ChatLimitError } from '../api'
import type { ChatLimit, ChatMessage } from '../api'
import { chatAllowanceQuery } from '../queries'

// Matches CHAT_MAX_CHARS in backend/app/config.py
export const MAX_CHARS = 250

const LIMIT_TEXT: Record<ChatLimit, (limit: number) => string> = {
  visitor: (limit) => `You've used your ${limit} messages for today.`,
  site: () => 'The AI Researcher is busy today. Try again tomorrow.',
}

type Props = {
  ticker: string
  // False until the company's Blurb has loaded; only Leaders can chat
  enabled: boolean
  // Shown instead of the counter when chat is off, such as for companies that aren't Leaders
  disabledReason?: string
  // The panel's opening messages (the Blurb), shown above the conversation
  children: ReactNode
}

// The conversation part of the AI Researcher panel: the message log, the input and the daily allowance.
// Remount with key={ticker} to start a new conversation for each company
export default function ChatWithAI({ ticker, enabled, disabledReason, children }: Props) {
  const queryClient = useQueryClient()
  const allowance = useQuery({ ...chatAllowanceQuery, enabled })
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [failed, setFailed] = useState(false)
  const [limitHit, setLimitHit] = useState<ChatLimit | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const alertId = useId()

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])

  const limit = allowance.data?.limit ?? 0
  const reason = limitHit ?? allowance.data?.reason ?? null
  const over = draft.length - MAX_CHARS
  const available = enabled && allowance.isSuccess && reason === null
  const canSend = available && !streaming && draft.trim() !== '' && over <= 0

  async function send(e: FormEvent) {
    e.preventDefault()
    if (!canSend) return
    const text = draft.trim()
    const history: ChatMessage[] = [...messages, { role: 'user', content: text }]
    setMessages([...history, { role: 'assistant', content: '' }])
    setDraft('')
    setFailed(false)
    setStreaming(true)
    let got = ''
    try {
      await api.chat(ticker, history, (chunk) => {
        got += chunk
        setMessages([...history, { role: 'assistant', content: got }])
      })
    } catch (err) {
      if (got === '') {
        // Nothing came back, so drop the turn and give the text back to try again
        setMessages(messages)
        setDraft(text)
      }
      if (err instanceof ChatLimitError) setLimitHit(err.reason)
      else setFailed(true)
    } finally {
      setStreaming(false)
      queryClient.invalidateQueries({ queryKey: chatAllowanceQuery.queryKey })
    }
  }

  let note: string | null = null
  if (disabledReason) note = disabledReason
  else if (allowance.isError) note = "Chat isn't available right now."
  else if (reason) note = LIMIT_TEXT[reason](limit)
  else if (allowance.data) note = `${allowance.data.remaining} of ${limit} messages left today`

  return (
    <>
      <div className="chat-messages" ref={scrollRef}>
        <div className="chat-intro" role="status">
          {children}
        </div>
        {messages.length > 0 && (
          <ol className="chat-log" role="log" aria-label="Conversation">
            {messages.map((m, i) => (
              <li key={i} className={m.role === 'user' ? 'chat-bubble chat-bubble-user' : 'chat-bubble'}>
                {m.content || (streaming && i === messages.length - 1 ? 'Thinking…' : '')}
              </li>
            ))}
          </ol>
        )}
        {failed && <p className="chat-bubble">Couldn't get an answer. Try again.</p>}
      </div>
      <form className="chat-form" onSubmit={send}>
        {over > 0 && (
          <p id={alertId} className="chat-alert" role="alert">
            Messages can be up to {MAX_CHARS} characters. You're {over} over.
          </p>
        )}
        {note && <p className="chat-note">{note}</p>}
        <div className="chat-compose">
          <input
            className="chat-input"
            type="text"
            placeholder="Message AI Researcher…"
            aria-label="Message"
            aria-invalid={over > 0}
            aria-describedby={over > 0 ? alertId : undefined}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={!available}
          />
          <button type="submit" className="chat-send" disabled={!canSend}>
            Send
          </button>
        </div>
      </form>
    </>
  )
}
