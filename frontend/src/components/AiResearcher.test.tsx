// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test } from 'vitest'
import AiResearcher from './AiResearcher'

// Vitest doesn't expose afterEach globally here, so RTL can't clean up on its own
afterEach(cleanup)

test('names the selected company and says the service is not available', () => {
  render(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  const button = screen.getByRole('button', { name: 'AI Researcher' })
  expect(screen.queryByRole('status')).toBeNull()

  fireEvent.click(button)

  const panel = screen.getByRole('status')
  expect(button.getAttribute('aria-expanded')).toBe('true')
  expect(panel.textContent).toContain('Moderna Inc.')
  expect(panel.textContent).toContain('MRNA')
  expect(panel.textContent).toContain('Service Not Available')
})

test('clicking again closes the panel', () => {
  render(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  const button = screen.getByRole('button', { name: 'AI Researcher' })

  fireEvent.click(button)
  fireEvent.click(button)

  expect(screen.queryByRole('status')).toBeNull()
  expect(button.getAttribute('aria-expanded')).toBe('false')
})

test('the close button closes the panel', () => {
  render(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  const toggle = screen.getByRole('button', { name: 'AI Researcher' })
  fireEvent.click(toggle)

  fireEvent.click(screen.getByRole('button', { name: 'Close AI Researcher' }))

  expect(screen.queryByRole('status')).toBeNull()
  expect(toggle.getAttribute('aria-expanded')).toBe('false')
})

test('follows the selection while open', () => {
  const { rerender } = render(<AiResearcher ticker="MRNA" name="Moderna Inc." />)
  fireEvent.click(screen.getByRole('button', { name: 'AI Researcher' }))

  rerender(<AiResearcher ticker="NVDA" name="Nvidia Corp." />)

  expect(screen.getByRole('status').textContent).toContain('Nvidia Corp.')
})
