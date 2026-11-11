// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import type { Leader } from '../api'
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

function renderTable(leaders: Leader[]) {
  const onSelect = vi.fn()
  render(<LeadersTable leaders={leaders} selected={null} onSelect={onSelect} stale={false} />)
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
