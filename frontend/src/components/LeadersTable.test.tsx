// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import type { Leader } from '../api'
import LeadersTable from './LeadersTable'

function leader(ticker: string, close: number): Leader {
  return {
    ticker,
    name: `${ticker} Inc.`,
    sector: 'Health Care',
    close,
    rs_rating: 90,
    rs_score: 1.2,
    ret_3m: 0.1,
    ret_12m: 0.3,
    rs_new_high: false,
    rating_change_1w: null,
  }
}

function renderTable(leaders: Leader[]) {
  const onSelect = vi.fn()
  render(<LeadersTable leaders={leaders} selected={null} onSelect={onSelect} loading={false} />)
  return onSelect
}

// Vitest doesn't expose afterEach globally here, so RTL can't clean up on its own
afterEach(cleanup)

test('close price links to the Yahoo Finance quote page in a new tab', () => {
  renderTable([leader('MRNA', 123.456)])
  const link = screen.getByRole('link', { name: '123.46' })

  expect(link.getAttribute('href')).toBe('https://finance.yahoo.com/quote/MRNA/')
  expect(link.getAttribute('target')).toBe('_blank')
  expect(link.getAttribute('rel')).toBe('noopener noreferrer')
})

test('ticker is URL-encoded in the link', () => {
  renderTable([leader('BRK/B', 1)])
  expect(screen.getByRole('link').getAttribute('href')).toBe(
    'https://finance.yahoo.com/quote/BRK%2FB/',
  )
})

test('clicking the close price does not select the row', () => {
  const onSelect = renderTable([leader('MRNA', 10)])
  fireEvent.click(screen.getByRole('link'))
  expect(onSelect).not.toHaveBeenCalled()
})

// The row's Enter handler calls preventDefault, which would stop the link from opening
test('pressing Enter on the close price is not swallowed by the row', () => {
  const onSelect = renderTable([leader('MRNA', 10)])
  const notPrevented = fireEvent.keyDown(screen.getByRole('link'), { key: 'Enter' })

  expect(notPrevented).toBe(true)
  expect(onSelect).not.toHaveBeenCalled()
})

test('clicking elsewhere in the row still selects it', () => {
  const onSelect = renderTable([leader('MRNA', 10)])
  fireEvent.click(screen.getByText('MRNA'))
  expect(onSelect).toHaveBeenCalledWith('MRNA')
})
