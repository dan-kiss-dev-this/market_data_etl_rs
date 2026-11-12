// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import type { ReactElement } from 'react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { api } from '../api'
import type { Blurb } from '../api'
import AiResearcher from './AiResearcher'

// Vitest doesn't expose afterEach globally here, so RTL can't clean up on its own
afterEach(cleanup)
afterEach(() => vi.restoreAllMocks())
beforeEach(() => {
  vi.spyOn(api, 'chatAllowance').mockResolvedValue({ remaining: 5, limit: 5, reason: null })
})

function renderWithQueries(ui: ReactElement) {
  const client = new QueryClient()
  const result = render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
  return { ...result, rerender: (next: ReactElement) => result.rerender(<QueryClientProvider client={client}>{next}</QueryClientProvider>) }
}

const blurb: Blurb = {
  ticker: 'NVDA',
  date: '2026-11-10',
  blurb: {
    what_they_sell: 'GPUs for AI data centers.',
    catalyst: 'Earnings beat and raised guidance on Nov 5.',
    category_position: 'The clear leader in AI accelerators.',
    momentum: 'RS 97 and at a new high.',
    risks: 'Export limits on China sales.',
  },
  headlines: [{ date: '2026-11-05', title: 'Nvidia beats and raises', publisher: 'Reuters', url: 'https://example.com/a' }],
  market: { status: 'Under pressure', breadth: 0.69 },
}

test('names the selected company while looking up its Blurb', () => {
  vi.spyOn(api, 'blurb').mockReturnValue(new Promise(() => {}))
  renderWithQueries(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  const button = screen.getByRole('button', { name: 'AI Researcher' })
  expect(screen.queryByRole('status')).toBeNull()

  fireEvent.click(button)

  const panel = screen.getByRole('status')
  expect(button.getAttribute('aria-expanded')).toBe('true')
  expect(panel.textContent).toContain('Moderna Inc.')
  expect(panel.textContent).toContain('MRNA')
  expect(panel.textContent).toContain('Looking up Moderna Inc.…')
})

test("doesn't look anything up until opened", () => {
  const spy = vi.spyOn(api, 'blurb').mockResolvedValue(null)
  renderWithQueries(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  expect(spy).not.toHaveBeenCalled()
})

test('shows the Blurb with the Market direction and cited sources', async () => {
  vi.spyOn(api, 'blurb').mockResolvedValue(blurb)
  renderWithQueries(<AiResearcher ticker="NVDA" name="Nvidia Corp." />)
  fireEvent.click(screen.getByRole('button', { name: 'AI Researcher' }))

  expect(await screen.findByText('Earnings beat and raised guidance on Nov 5.')).toBeTruthy()
  const panel = screen.getByRole('status')
  expect(panel.textContent).toContain('S&P 500: Under pressure')
  expect(panel.textContent).toContain('Breadth 69%')
  expect(panel.textContent).toContain('Updated 2026-11-10')
  expect(screen.getByRole('link', { name: 'Nvidia beats and raises' }).getAttribute('href')).toBe('https://example.com/a')
  expect(screen.getByText('Online')).toBeTruthy()
  expect(await screen.findByText('5 of 5 messages left today')).toBeTruthy()
  expect((screen.getByRole('textbox', { name: 'Message' }) as HTMLInputElement).disabled).toBe(false)
})

test('says there is no current Blurb for a company that is not a Leader', async () => {
  vi.spyOn(api, 'blurb').mockResolvedValue(null)
  renderWithQueries(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  fireEvent.click(screen.getByRole('button', { name: 'AI Researcher' }))

  expect(await screen.findByText('No current Blurb. Blurbs cover the top 50 by RS rating.')).toBeTruthy()
  expect(screen.getByText('Offline')).toBeTruthy()
  expect(screen.getByText('Chat only works for Leaders, the top 50 companies by RS rating.')).toBeTruthy()
  expect((screen.getByRole('textbox', { name: 'Message' }) as HTMLInputElement).disabled).toBe(true)
})

test('says so when the Blurb fails to load', async () => {
  vi.spyOn(api, 'blurb').mockRejectedValue(new Error('500'))
  renderWithQueries(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  fireEvent.click(screen.getByRole('button', { name: 'AI Researcher' }))

  expect(await screen.findByText("Couldn't load the Blurb right now. Try again later.")).toBeTruthy()
})

test('clicking again closes the panel', () => {
  vi.spyOn(api, 'blurb').mockResolvedValue(null)
  renderWithQueries(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  const button = screen.getByRole('button', { name: 'AI Researcher' })

  fireEvent.click(button)
  fireEvent.click(button)

  expect(screen.queryByRole('status')).toBeNull()
  expect(button.getAttribute('aria-expanded')).toBe('false')
})

test('the close button closes the panel', () => {
  vi.spyOn(api, 'blurb').mockResolvedValue(null)
  renderWithQueries(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  const toggle = screen.getByRole('button', { name: 'AI Researcher' })
  fireEvent.click(toggle)

  fireEvent.click(screen.getByRole('button', { name: 'Close AI Researcher' }))

  expect(screen.queryByRole('status')).toBeNull()
  expect(toggle.getAttribute('aria-expanded')).toBe('false')
})

test('follows the selection while open', async () => {
  vi.spyOn(api, 'blurb').mockImplementation(async (ticker) => (ticker === 'NVDA' ? blurb : null))
  const { rerender } = renderWithQueries(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  fireEvent.click(screen.getByRole('button', { name: 'AI Researcher' }))

  rerender(<AiResearcher ticker="NVDA" name="Nvidia Corp." />)

  expect(screen.getByRole('status').textContent).toContain('Nvidia Corp.')
  expect(await screen.findByText('GPUs for AI data centers.')).toBeTruthy()
})
