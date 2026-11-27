// @vitest-environment jsdom
/// <reference types="node" />
import { readFileSync } from 'node:fs'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import type { Benchmark, Leader } from '../api'
import LeadersTable, { LeadersTableSkeleton } from './LeadersTable'

function leader(ticker: string, ret3m = 0.1): Leader {
  return {
    ticker,
    name: `${ticker} Inc.`,
    sector: 'Health Care',
    close: 50,
    rs_rating: 90,
    rs_score: 1.2,
    ret_3m: ret3m,
    ret_12m: 0.3,
    rs_new_high: false,
    rating_change_1w: null,
  }
}

const spy: Benchmark = { ticker: 'SPY', name: 'SPDR S&P 500 ETF', date: '2026-11-26', close: 600, ret_3m: 0.042, ret_12m: 0.151 }

function renderTable(leaders: Leader[], benchmark?: Benchmark) {
  const onSelect = vi.fn()
  render(<LeadersTable leaders={leaders} benchmark={benchmark} selected={null} onSelect={onSelect} stale={false} />)
  return onSelect
}

// Vitest doesn't expose afterEach globally here, so RTL can't clean up on its own
afterEach(cleanup)

// jsdom doesn't load index.css, so both of Pct's spans count toward the link text
test('3M return links to the Yahoo Finance quote page in a new tab', () => {
  renderTable([leader('MRNA', 0.234)])
  const link = screen.getByRole('link', { name: /^\+23\.4%/ })

  expect(link.getAttribute('href')).toBe('https://finance.yahoo.com/quote/MRNA/')
  expect(link.getAttribute('target')).toBe('_blank')
  expect(link.getAttribute('rel')).toBe('noopener noreferrer')
})

test('ticker is URL-encoded in the link', () => {
  renderTable([leader('BRK/B')])
  expect(screen.getByRole('link').getAttribute('href')).toBe(
    'https://finance.yahoo.com/quote/BRK%2FB/',
  )
})

test('clicking the 3M return does not select the row', () => {
  const onSelect = renderTable([leader('MRNA')])
  fireEvent.click(screen.getByRole('link'))
  expect(onSelect).not.toHaveBeenCalled()
})

// The row's Enter handler calls preventDefault, which would stop the link from opening
test('pressing Enter on the 3M return is not swallowed by the row', () => {
  const onSelect = renderTable([leader('MRNA')])
  const notPrevented = fireEvent.keyDown(screen.getByRole('link'), { key: 'Enter' })

  expect(notPrevented).toBe(true)
  expect(onSelect).not.toHaveBeenCalled()
})

test('clicking elsewhere in the row still selects it', () => {
  const onSelect = renderTable([leader('MRNA')])
  fireEvent.click(screen.getByText('MRNA'))
  expect(onSelect).toHaveBeenCalledWith('MRNA')
})

test('close price is no longer a link', () => {
  renderTable([leader('MRNA')])
  expect(screen.getByText('50.00').closest('a')).toBeNull()
  expect(screen.getAllByRole('link')).toHaveLength(1)
})

test('the skeleton keeps the real header over shimmer rows that span every column', () => {
  const { container } = render(<LeadersTableSkeleton rows={4} />)

  expect([...container.querySelectorAll('th')].map((th) => th.textContent)).toEqual([
    '#', 'Stock', 'RS Rating', '1W', '3M', '12M', 'Close',
  ])
  const cells = [...container.querySelectorAll('tbody td')]
  expect(cells).toHaveLength(4)
  expect(cells.every((td) => td.getAttribute('colspan') === '7' && td.querySelector('.skeleton-row'))).toBe(true)
})

test('the SPY row sits above the Leaders with its returns and close, and no rank, rating or 1W', () => {
  renderTable([leader('MRNA')], spy)
  const [, spyRow, first] = screen.getAllByRole('row')

  expect(spyRow.textContent).toContain('SPY')
  expect(spyRow.textContent).toContain('+4.2%')
  expect(spyRow.textContent).toContain('+15.1%')
  expect(spyRow.textContent).toContain('600.00')
  const cells = [...spyRow.querySelectorAll('td')].map((td) => td.textContent)
  expect([cells[0], cells[2], cells[3]]).toEqual(['', '–', '–'])
  // The Leaders are still numbered from 1
  expect(first.querySelector('td')?.textContent).toBe('1')
})

test('clicking or pressing Enter on the SPY row selects SPY', () => {
  const onSelect = renderTable([leader('MRNA')], spy)
  const spyRow = screen.getAllByRole('row')[1]

  fireEvent.click(spyRow)
  fireEvent.keyDown(spyRow, { key: 'Enter' })
  expect(onSelect.mock.calls).toEqual([['SPY'], ['SPY']])
})

// Read from disk: Vitest stubs CSS imports (even ?raw) to empty strings
const css = readFileSync(`${import.meta.dirname}/../index.css`, 'utf8')

// The declarations of the first rule with exactly this selector, as a property → value map
function rule(selector: string) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const body = css.match(new RegExp(`(?:^|\\n)${escaped}\\s*\\{([^}]*)\\}`))?.[1] ?? ''
  return Object.fromEntries(
    body.replace(/\/\*[\s\S]*?\*\//g, '').split(';').map((d) => d.split(':').map((p) => p.trim())).filter((d) => d.length === 2),
  )
}

// jsdom has no layout, so check the CSS itself: the row must stick exactly where the header ends
test('the SPY row sticks just under the sticky header, so it never scrolls out of view', () => {
  const head = rule('.leaders th')
  const spy = rule('.leaders tbody tr[data-benchmark] td')
  const headHeight = rule('.leaders')['--leaders-head-height']
  const [padTop, , padBottom = padTop] = head.padding.split(/\s+/).map(parseFloat)

  expect(spy.position).toBe('sticky')
  expect(spy.top).toBe('var(--leaders-head-height)')
  expect(`${padTop + parseFloat(head['line-height']) + padBottom}px`).toBe(headHeight)
  // A collapsed border scrolls away from a sticky cell, leaving a stripe the Leaders show through
  expect(head['border-bottom']).toBeUndefined()
  expect(head['box-shadow']).toMatch(/^inset 0 -1px 0 /)
  // Above the Leaders scrolling beneath it, below the header
  expect(Number(head['z-index'])).toBeGreaterThan(Number(spy['z-index']))
  expect(spy.background).toBeTruthy()
})
