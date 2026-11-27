import type { KeyboardEvent, ReactNode } from 'react'
import type { Benchmark, Leader } from '../api'

type Props = {
  leaders: Leader[]
  benchmark?: Benchmark
  selected: string | null
  onSelect: (ticker: string) => void
  stale: boolean
}

const pct = (v: number) => `${v >= 0 ? '+' : ''}${(v * 100).toFixed(1)}%`

// Round from the one-decimal value shown on desktop, half away from zero, so +22.5% reads +23%
function pctWhole(v: number) {
  const tenth = Number((v * 100).toFixed(1))
  const whole = Math.sign(tenth) * Math.round(Math.abs(tenth))
  return `${whole >= 0 ? '+' : ''}${whole}%`
}

// Only one span is displayed at a time (see .pct-full / .pct-whole in index.css)
function Pct({ value }: { value: number }) {
  return (
    <>
      <span className="pct-full">{pct(value)}</span>
      <span className="pct-whole">{pctWhole(value)}</span>
    </>
  )
}

function Change({ value }: { value: number | null }) {
  if (value === null) return <span className="muted">–</span>
  if (value === 0) return <span className="muted">0</span>
  const up = value > 0
  return (
    <span className={up ? 'delta-up' : 'delta-down'}>
      <span aria-hidden="true">{up ? '▲' : '▼'}</span> {Math.abs(value)}
      <span className="sr-only">{up ? ' up' : ' down'}</span>
    </span>
  )
}

// Click, Enter or Space selects a row
function selectable(ticker: string, selected: string | null, onSelect: (ticker: string) => void) {
  return {
    className: ticker === selected ? 'selected' : undefined,
    'aria-selected': ticker === selected,
    tabIndex: 0,
    onClick: () => onSelect(ticker),
    onKeyDown: (e: KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        onSelect(ticker)
      }
    },
  }
}

function QuoteLink({ ticker, children }: { ticker: string; children: ReactNode }) {
  return (
    <a
      className="quote-link"
      href={`https://finance.yahoo.com/quote/${encodeURIComponent(ticker)}/`}
      target="_blank"
      rel="noopener noreferrer"
      title={`Open ${ticker} on Yahoo Finance`}
      onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => e.stopPropagation()}
    >
      {children}
    </a>
  )
}

const COLUMNS = 7

function Head() {
  return (
    <thead>
      <tr>
        <th className="num">#</th>
        <th>Stock</th>
        <th className="num">RS Rating</th>
        <th className="num" title="Rating change vs. 5 trading days ago">1W</th>
        <th className="num">3M</th>
        <th className="num">12M</th>
        <th className="num">Close</th>
      </tr>
    </thead>
  )
}

// The real header over shimmer rows, in the same box, for before the first leaders arrive
export function LeadersTableSkeleton({ rows = 10 }: { rows?: number }) {
  return (
    <div className="table-wrap" aria-busy="true" aria-label="Loading leaders">
      <table className="leaders">
        <Head />
        <tbody aria-hidden="true">
          {Array.from({ length: rows }, (_, i) => (
            <tr key={i}>
              <td colSpan={COLUMNS}>
                <div className="skeleton skeleton-row" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function LeadersTable({ leaders, benchmark, selected, onSelect, stale }: Props) {
  return (
    <div className={`table-wrap${stale ? ' is-loading' : ''}`} aria-busy={stale}>
      <table className="leaders">
        <Head />
        <tbody>
          {/* Not a Leader, so it is unnumbered and has no rating; it's there to compare returns with */}
          {benchmark && (
            <tr {...selectable(benchmark.ticker, selected, onSelect)} data-benchmark="">
              <td className="num muted"></td>
              <td>
                <div className="stock">
                  <span className="ticker">{benchmark.ticker}</span>
                </div>
                <div className="name">{benchmark.name}</div>
              </td>
              <td className="num muted">–</td>
              <td className="num muted">–</td>
              <td className="num">
                <QuoteLink ticker={benchmark.ticker}>
                  <Pct value={benchmark.ret_3m} />
                </QuoteLink>
              </td>
              <td className="num"><Pct value={benchmark.ret_12m} /></td>
              <td className="num">{benchmark.close.toFixed(2)}</td>
            </tr>
          )}
          {leaders.map((l, i) => (
            <tr key={l.ticker} {...selectable(l.ticker, selected, onSelect)}>
              <td className="num muted">{i + 1}</td>
              <td>
                <div className="stock">
                  <span className="ticker">{l.ticker}</span>
                  {l.rs_new_high && (
                    <span className="new-high" title="RS line at a 52-week high">
                      <span className="sr-only">RS line at a 52-week high</span>
                    </span>
                  )}
                </div>
                <div className="name">{l.name}</div>
              </td>
              <td className="num">
                <div className="rating">
                  <span className="rating-value">{l.rs_rating}</span>
                  <span className="meter" aria-hidden="true">
                    <span style={{ width: `${l.rs_rating}%` }} />
                  </span>
                </div>
              </td>
              <td className="num"><Change value={l.rating_change_1w} /></td>
              <td className="num">
                <QuoteLink ticker={l.ticker}>
                  <Pct value={l.ret_3m} />
                </QuoteLink>
              </td>
              <td className="num"><Pct value={l.ret_12m} /></td>
              <td className="num">{l.close.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
