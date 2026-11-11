// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { api } from './api'
import type { Leader, Status, TickerDetail } from './api'
import App from './App'

afterEach(cleanup)

beforeEach(() => {
  vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener() {}, removeEventListener() {} }))
  // RsChart's ResponsiveContainer needs it, and jsdom has none
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      disconnect() {}
    },
  )
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

const status: Status = {
  first_date: '2025-01-02',
  latest_date: '2026-11-10',
  rated_date: '2026-11-10',
  trading_days: 470,
  tickers: 500,
  benchmark: 'SPY',
}

const leader = (ticker: string): Leader => ({
  ticker,
  name: `${ticker} Inc.`,
  sector: 'Health Care',
  close: 50,
  rs_rating: 90,
  rs_score: 1.2,
  ret_3m: 0.1,
  ret_12m: 0.3,
  rs_new_high: false,
  rating_change_1w: null,
})

const detail = (ticker: string): TickerDetail => ({
  ticker,
  name: `${ticker} Inc.`,
  sector: 'Health Care',
  series: [{ date: '2026-11-10', close: 50, rs_line: 1, rs_rating: 90 }],
})

// A promise the test settles by hand, to hold a request open
function pending<T>() {
  let resolve!: (v: T) => void
  let reject!: (e: Error) => void
  const promise = new Promise<T>((res, rej) => ((resolve = res), (reject = rej)))
  return { promise, resolve, reject }
}

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  )
}

const tableSkeleton = (c: HTMLElement) => c.querySelector('[aria-label="Loading leaders"]')
const chartSkeleton = (c: HTMLElement) => c.querySelector('[aria-label="Loading charts"]')

test('renders the header and filters at once, with skeletons where data goes, until status loads', async () => {
  const s = pending<Status>()
  vi.spyOn(api, 'status').mockReturnValue(s.promise)
  vi.spyOn(api, 'sectors').mockResolvedValue([])
  vi.spyOn(api, 'leaders').mockResolvedValue([])
  const { container } = renderApp()

  expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('S&P 500 RS Leaders')
  expect(container.querySelectorAll('.app-header .skeleton-text')).toHaveLength(2)
  expect(screen.getByRole('toolbar', { name: 'Filters' })).toBeTruthy()
  expect(screen.getByRole('group', { name: 'Chart range' })).toBeTruthy()
  expect(tableSkeleton(container)).not.toBeNull()
  expect(chartSkeleton(container)?.querySelectorAll('.skeleton-bolt')).toHaveLength(3)

  await act(async () => s.resolve({ ...status, rated_date: null }))
  expect(await screen.findByText('No RS ratings yet')).toBeTruthy()
  expect(container.querySelector('.skeleton')).toBeNull()
  expect(screen.queryByRole('toolbar', { name: 'Filters' })).toBeNull()
})

test('the benchmark, date and sectors fill in where their skeletons were', async () => {
  const sectors = pending<string[]>()
  vi.spyOn(api, 'status').mockResolvedValue(status)
  vi.spyOn(api, 'sectors').mockReturnValue(sectors.promise)
  vi.spyOn(api, 'leaders').mockResolvedValue([leader('AAA')])
  vi.spyOn(api, 'ticker').mockImplementation((t) => Promise.resolve(detail(t)))
  const { container } = renderApp()

  expect(await screen.findByText('2026-11-10')).toBeTruthy()
  expect(container.querySelector('.app-header')?.textContent).toContain('vs. SPY, weighted')
  expect(container.querySelector('.app-header .skeleton-text')).toBeNull()
  const select = screen.getByRole('combobox') as HTMLSelectElement
  expect(select.disabled).toBe(true)

  await act(async () => sectors.resolve(['Tech']))
  await waitFor(() => expect((screen.getByRole('combobox') as HTMLSelectElement).disabled).toBe(false))
  expect([...screen.getByRole('combobox').querySelectorAll('option')].map((o) => o.textContent)).toEqual([
    'All sectors',
    'Tech',
  ])
})

test('sectors and leaders start loading without waiting for status', () => {
  vi.spyOn(api, 'status').mockReturnValue(new Promise(() => {}))
  const sectors = vi.spyOn(api, 'sectors').mockResolvedValue([])
  const leaders = vi.spyOn(api, 'leaders').mockResolvedValue([])
  renderApp()

  expect(sectors).toHaveBeenCalled()
  expect(leaders).toHaveBeenCalledWith(null)
})

test('the table and the chart each show their own skeleton until their data arrives', async () => {
  const t = pending<TickerDetail>()
  vi.spyOn(api, 'status').mockResolvedValue(status)
  vi.spyOn(api, 'sectors').mockResolvedValue([])
  vi.spyOn(api, 'leaders').mockResolvedValue([leader('AAA')])
  vi.spyOn(api, 'ticker').mockReturnValue(t.promise)
  const { container } = renderApp()

  expect(await screen.findByText('AAA')).toBeTruthy()
  expect(tableSkeleton(container)).toBeNull()
  expect(chartSkeleton(container)).not.toBeNull()

  await act(async () => t.resolve(detail('AAA')))
  await waitFor(() => expect(container.querySelector('[aria-label="AAA charts"]')).not.toBeNull())
  expect(chartSkeleton(container)).toBeNull()
})

test('the AI Researcher button appears once a stock is charted, for that stock', async () => {
  vi.spyOn(api, 'status').mockResolvedValue(status)
  vi.spyOn(api, 'sectors').mockResolvedValue([])
  vi.spyOn(api, 'leaders').mockResolvedValue([leader('AAA')])
  vi.spyOn(api, 'ticker').mockImplementation((t) => Promise.resolve(detail(t)))
  renderApp()

  fireEvent.click(await screen.findByRole('button', { name: 'AI Researcher' }))
  expect(screen.getByRole('status').textContent).toContain("You've selected AAA Inc. (AAA) to research.")
})

test('changing sector keeps the old rows on screen, dimmed, until the new ones arrive', async () => {
  const tech = pending<Leader[]>()
  vi.spyOn(api, 'status').mockResolvedValue(status)
  vi.spyOn(api, 'sectors').mockResolvedValue(['Tech'])
  vi.spyOn(api, 'leaders').mockImplementation((sector) =>
    sector === 'Tech' ? tech.promise : Promise.resolve([leader('AAA')]),
  )
  vi.spyOn(api, 'ticker').mockImplementation((t) => Promise.resolve(detail(t)))
  const { container } = renderApp()
  const rows = () => [...container.querySelectorAll('.leaders .ticker')].map((el) => el.textContent)
  await waitFor(() => expect(rows()).toEqual(['AAA']))

  fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Tech' } })
  await waitFor(() => expect(container.querySelector('.table-wrap.is-loading')).not.toBeNull())
  expect(rows()).toEqual(['AAA'])
  expect(tableSkeleton(container)).toBeNull()

  await act(async () => tech.resolve([leader('BBB')]))
  await waitFor(() => expect(rows()).toEqual(['BBB']))
  expect(container.querySelector('.table-wrap.is-loading')).toBeNull()
})

test('a failed request shows the load error', async () => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
  vi.spyOn(api, 'status').mockRejectedValue(new Error('offline'))
  vi.spyOn(api, 'sectors').mockResolvedValue([])
  vi.spyOn(api, 'leaders').mockResolvedValue([])
  renderApp()

  expect(await screen.findByText('Could not load data')).toBeTruthy()
  expect(screen.getByText('offline')).toBeTruthy()
})
