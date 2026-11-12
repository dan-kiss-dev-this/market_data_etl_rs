export type Status = {
  first_date: string | null
  latest_date: string | null
  rated_date: string | null
  trading_days: number
  tickers: number
  benchmark: string
}

export type Leader = {
  ticker: string
  name: string
  sector: string
  close: number
  rs_rating: number
  rs_score: number
  ret_3m: number
  ret_12m: number
  rs_new_high: boolean
  rating_change_1w: number | null
}

export type Point = {
  date: string
  close: number
  rs_line: number
  rs_rating: number | null
}

export type TickerDetail = {
  ticker: string
  name: string
  sector: string
  series: Point[]
}

export type MarketDirection = {
  status: 'Uptrend' | 'Under pressure' | 'Downtrend'
  // Share (0-1) of S&P 500 companies above their own 50-day average
  breadth: number | null
}

export type Headline = {
  date: string
  title: string
  publisher: string
  url: string
}

export type BlurbFields = {
  what_they_sell: string
  catalyst: string
  category_position: string
  momentum: string
  risks: string
}

export type Blurb = {
  ticker: string
  date: string
  blurb: BlurbFields
  headlines: Headline[]
  market: MarketDirection | null
}

export type ChatMessage = { role: 'user' | 'assistant'; content: string }

// Why no messages are left: the visitor used theirs today, or the site hit its daily cap
export type ChatLimit = 'visitor' | 'site'

export type ChatAllowance = { remaining: number; limit: number; reason: ChatLimit | null }

export class ChatLimitError extends Error {
  reason: ChatLimit
  constructor(reason: ChatLimit) {
    super(`Chat limit reached (${reason})`)
    this.reason = reason
  }
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} (${url})`)
  return res.json()
}

export const api = {
  status: () => getJson<Status>('/api/rs/status'),
  sectors: () => getJson<string[]>('/api/rs/sectors'),
  leaders: (sector: string | null, limit = 50) => {
    const params = new URLSearchParams({ limit: String(limit) })
    if (sector) params.set('sector', sector)
    return getJson<Leader[]>(`/api/rs/leaders?${params}`)
  },
  ticker: (ticker: string) => getJson<TickerDetail>(`/api/rs/${encodeURIComponent(ticker)}`),
  // null when the company has no current Blurb (only Leaders get one)
  blurb: async (ticker: string): Promise<Blurb | null> => {
    const url = `/api/rs/${encodeURIComponent(ticker)}/blurb`
    const res = await fetch(url)
    if (res.status === 404) return null
    if (!res.ok) throw new Error(`${res.status} ${res.statusText} (${url})`)
    return res.json()
  },
  chatAllowance: () => getJson<ChatAllowance>('/api/chat/allowance'),
  // Streams the reply to the last message through onText
  chat: async (ticker: string, messages: ChatMessage[], onText: (text: string) => void): Promise<void> => {
    const url = `/api/rs/${encodeURIComponent(ticker)}/chat`
    const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages }) })
    if (res.status === 429) throw new ChatLimitError((await res.json()).detail.reason)
    if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText} (${url})`)
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      onText(decoder.decode(value, { stream: true }))
    }
  },
}

// IBD needs 252 prior trading days before the first rating
export const MIN_BARS = 253
