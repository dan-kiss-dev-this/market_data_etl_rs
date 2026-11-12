// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { api, ChatLimitError } from '../api'
import ChatWithAI from './ChatWithAI'

afterEach(cleanup)
afterEach(() => vi.restoreAllMocks())
beforeEach(() => {
  vi.spyOn(api, 'chatAllowance').mockResolvedValue({ remaining: 5, limit: 5, reason: null })
})

function renderChat(props: { enabled?: boolean; disabledReason?: string } = {}) {
  const client = new QueryClient()
  return render(
    <QueryClientProvider client={client}>
      <ChatWithAI ticker="NVDA" enabled={props.enabled ?? true} disabledReason={props.disabledReason}>
        <p>Blurb</p>
      </ChatWithAI>
    </QueryClientProvider>,
  )
}

const input = () => screen.getByRole('textbox', { name: 'Message' }) as HTMLInputElement
const send = () => screen.getByRole('button', { name: 'Send' }) as HTMLButtonElement

test('shows how many messages are left today', async () => {
  renderChat()
  expect(await screen.findByText('5 of 5 messages left today')).toBeTruthy()
  expect(send().disabled).toBe(true) // nothing typed yet
})

test('alerts and disables Send when a message is over 250 characters', async () => {
  renderChat()
  await screen.findByText('5 of 5 messages left today')

  fireEvent.change(input(), { target: { value: 'x'.repeat(250) } })
  expect(screen.queryByRole('alert')).toBeNull()
  expect(send().disabled).toBe(false)

  fireEvent.change(input(), { target: { value: 'x'.repeat(253) } })
  expect(screen.getByRole('alert').textContent).toBe("Messages can be up to 250 characters. You're 3 over.")
  expect(send().disabled).toBe(true)
  expect(input().getAttribute('aria-invalid')).toBe('true')
})

test('is off for companies that are not Leaders', () => {
  const allowance = vi.spyOn(api, 'chatAllowance')
  renderChat({ enabled: false, disabledReason: 'Chat only works for Leaders, the top 50 companies by RS rating.' })
  expect(screen.getByText('Chat only works for Leaders, the top 50 companies by RS rating.')).toBeTruthy()
  expect(input().disabled).toBe(true)
  expect(send().disabled).toBe(true)
  expect(allowance).not.toHaveBeenCalled()
})

test('streams the reply into the conversation', async () => {
  const chat = vi.spyOn(api, 'chat').mockImplementation(async (_ticker, _messages, onText) => {
    onText('Nvidia ')
    onText('leads AI chips.')
  })
  renderChat()
  await screen.findByText('5 of 5 messages left today')

  fireEvent.change(input(), { target: { value: '  Who are its rivals?  ' } })
  fireEvent.click(send())

  expect(await screen.findByText('Nvidia leads AI chips.')).toBeTruthy()
  const log = screen.getByRole('log')
  expect(log.textContent).toContain('Who are its rivals?')
  expect(chat).toHaveBeenCalledWith('NVDA', [{ role: 'user', content: 'Who are its rivals?' }], expect.any(Function))
  expect(input().value).toBe('')
})

test('says when the visitor has used their messages, and keeps the text', async () => {
  vi.spyOn(api, 'chat').mockRejectedValue(new ChatLimitError('visitor'))
  renderChat()
  await screen.findByText('5 of 5 messages left today')

  fireEvent.change(input(), { target: { value: 'One more?' } })
  fireEvent.click(send())

  expect(await screen.findByText("You've used your 5 messages for today.")).toBeTruthy()
  expect(screen.queryByRole('log')).toBeNull()
  expect(input().value).toBe('One more?')
  expect(input().disabled).toBe(true)
})

test('says when the site is out of messages for the day', async () => {
  vi.spyOn(api, 'chatAllowance').mockResolvedValue({ remaining: 0, limit: 5, reason: 'site' })
  renderChat()
  expect(await screen.findByText('The AI Researcher is busy today. Try again tomorrow.')).toBeTruthy()
  expect(input().disabled).toBe(true)
})

test('says so when the answer fails', async () => {
  vi.spyOn(api, 'chat').mockRejectedValue(new Error('502'))
  renderChat()
  await screen.findByText('5 of 5 messages left today')

  fireEvent.change(input(), { target: { value: 'Rivals?' } })
  fireEvent.click(send())

  expect(await screen.findByText("Couldn't get an answer. Try again.")).toBeTruthy()
  expect(input().value).toBe('Rivals?')
})
