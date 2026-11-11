import { usePrefetchQuery, useSuspenseQueries, useSuspenseQuery } from '@tanstack/react-query'
import { Suspense, useDeferredValue, useState } from 'react'
import type { ReactNode } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import type { FallbackProps } from 'react-error-boundary'
import { MIN_BARS } from './api'
import AiResearcher from './components/AiResearcher'
import LeadersTable, { LeadersTableSkeleton } from './components/LeadersTable'
import RsChart, { ChartSkeleton } from './components/RsChart'
import { leadersQuery, sectorsQuery, statusQuery, tickerQuery } from './queries'
import { RANGES } from './ranges'
import type { Range } from './ranges'
import { STACKED, useMediaQuery } from './useMediaQuery'

// The page frame renders at once, and only the parts that need data suspend, each behind a
// skeleton of its own size, so nothing moves when data arrives. After that, a sector or stock
// change keeps the old content on screen, dimmed, via useDeferredValue.
function App() {
  return (
    <main className="app">
      <ErrorBoundary FallbackComponent={LoadError}>
        <Dashboard />
      </ErrorBoundary>
    </main>
  )
}

function LoadError({ error }: FallbackProps) {
  return (
    <div className="notice">
      <h2>Could not load data</h2>
      <p>{error instanceof Error ? error.message : String(error)}</p>
      <p className="muted">Is the backend running? <code>cd backend && uv run fastapi dev app/main.py</code></p>
    </div>
  )
}

// A word-sized shimmer, for a value inside a line of text
function TextSkeleton({ width }: { width: string }) {
  return <span className="skeleton skeleton-text" style={{ width }} aria-hidden="true" />
}

function Benchmark() {
  return useSuspenseQuery(statusQuery).data.benchmark
}

function RatedDate() {
  const { rated_date } = useSuspenseQuery(statusQuery).data
  return <p>{rated_date && <>Ratings as of <strong>{rated_date}</strong>.</>}</p>
}

type SectorSelectProps = { value: string | null; onChange: (sector: string | null) => void }

function SectorSelect({ value, onChange }: SectorSelectProps) {
  const { data: sectors } = useSuspenseQuery(sectorsQuery)
  return (
    <select value={value ?? ''} onChange={(e) => onChange(e.target.value || null)}>
      <option value="">All sectors</option>
      {sectors.map((s) => (
        <option key={s} value={s}>{s}</option>
      ))}
    </select>
  )
}

function Dashboard() {
  const [sector, setSector] = useState<string | null>(null)
  const shownSector = useDeferredValue(sector)
  const [range, setRange] = useState<Range>('1Y')
  const isStacked = useMediaQuery(STACKED)
  // Start these now rather than once status has loaded, so the first load runs in parallel
  usePrefetchQuery(sectorsQuery)
  usePrefetchQuery(leadersQuery(shownSector))

  // When the layout stacks, the range picker sits directly above the chart it controls, below the table
  const rangePicker = (
    <div className="segmented" role="group" aria-label="Chart range">
      {(Object.keys(RANGES) as Range[]).map((r) => (
        <button key={r} type="button" aria-pressed={r === range} onClick={() => setRange(r)}>
          {r}
        </button>
      ))}
    </div>
  )

  const filters = (
    <div className="filters" role="toolbar" aria-label="Filters">
      <label>
        <span className="muted">Sector</span>
        <Suspense
          fallback={
            <select disabled aria-busy="true">
              <option>All sectors</option>
            </select>
          }
        >
          <SectorSelect value={sector} onChange={setSector} />
        </Suspense>
      </label>
      {!isStacked && rangePicker}
      <span className="legend-note muted">
        <span className="new-high" aria-hidden="true" /> RS line at a 52-week high
      </span>
    </div>
  )

  const boardSkeleton = (
    <>
      <LeadersTableSkeleton />
      {isStacked && rangePicker}
      <ChartSkeleton />
    </>
  )

  return (
    <>
      <header className="app-header">
        <h1>S&amp;P 500 RS Leaders</h1>
        <p className="muted">
          IBD-style Relative Strength: 12-month performance vs.{' '}
          <Suspense fallback={<TextSkeleton width="3.5ch" />}>
            <Benchmark />
          </Suspense>
          , weighted toward the latest quarter, ranked 1–99.
        </p>
        <Suspense
          fallback={
            <p>
              Ratings as of <TextSkeleton width="10ch" />.
            </p>
          }
        >
          <RatedDate />
        </Suspense>
      </header>

      <Suspense
        fallback={
          <>
            {filters}
            <div className="layout">{boardSkeleton}</div>
          </>
        }
      >
        <Body
          filters={filters}
          boardSkeleton={boardSkeleton}
          board={
            <Board
              sector={shownSector}
              stale={sector !== shownSector}
              range={range}
              rangePicker={isStacked && rangePicker}
            />
          }
        />
      </Suspense>
    </>
  )
}

type BodyProps = { filters: ReactNode; boardSkeleton: ReactNode; board: ReactNode }

// Until the first ratings exist there is nothing to filter or chart, only how to get them
function Body({ filters, boardSkeleton, board }: BodyProps) {
  const { data: status } = useSuspenseQuery(statusQuery)
  if (!status.rated_date) {
    return (
      <div className="notice">
        <h2>No RS ratings yet</h2>
        <p>
          {status.trading_days} of {MIN_BARS} trading days loaded. Each rating needs 12 months of prices.
        </p>
        <p className="muted">
          Run the pipeline from <code>backend/</code>: <code>uv run python -m app.etl</code>, then reload.
        </p>
      </div>
    )
  }
  return (
    <>
      {filters}
      <div className="layout">
        <Suspense fallback={boardSkeleton}>{board}</Suspense>
      </div>
    </>
  )
}

type BoardProps = {
  sector: string | null
  stale: boolean
  range: Range
  rangePicker: ReactNode
}

// The table and the chart for one sector
function Board({ sector, stale, range, rangePicker }: BoardProps) {
  const { data: rows } = useSuspenseQuery(leadersQuery(sector))
  const [pick, setPick] = useState<string | null>(null)
  // Keep the pick if it survived the filter; otherwise show the leader
  const selected = pick && rows.some((r) => r.ticker === pick) ? pick : (rows[0]?.ticker ?? null)
  const shownTicker = useDeferredValue(selected)

  return (
    <>
      <LeadersTable leaders={rows} selected={selected} onSelect={setPick} stale={stale} />
      {rangePicker}
      {shownTicker ? (
        <Suspense fallback={<ChartSkeleton />}>
          <Chart ticker={shownTicker} stale={selected !== shownTicker} range={range} />
        </Suspense>
      ) : (
        <div className="chart-card muted">No stocks in this sector</div>
      )}
    </>
  )
}

type ChartProps = { ticker: string; stale: boolean; range: Range }

function Chart({ ticker, ...rest }: ChartProps) {
  const [{ data: status }, { data: detail }] = useSuspenseQueries({ queries: [statusQuery, tickerQuery(ticker)] })
  return (
    <>
      <RsChart detail={detail} benchmark={status.benchmark} {...rest} />
      {/* Floats over the page (position: fixed), so it takes no space in the layout */}
      <AiResearcher ticker={detail.ticker} name={detail.name} />
    </>
  )
}

export default App
