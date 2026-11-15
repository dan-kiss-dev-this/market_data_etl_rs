// @vitest-environment jsdom
import { afterEach, expect, test } from 'vitest'
import { loadAnalytics } from './analytics'

const BEACON_SRC = 'https://static.cloudflareinsights.com/beacon.min.js'

afterEach(() => {
  document.head.innerHTML = ''
})

test('production builds add the Cloudflare beacon with the site token', () => {
  loadAnalytics(true)

  const scripts = document.head.querySelectorAll(`script[src="${BEACON_SRC}"]`)
  expect(scripts).toHaveLength(1)
  const script = scripts[0] as HTMLScriptElement
  expect(script.defer).toBe(true)
  expect(JSON.parse(script.dataset.cfBeacon!)).toEqual({ token: 'd0ed2b6d93aa44bf934180e1480e87de' })
})

test('dev builds add no beacon', () => {
  loadAnalytics(false)

  expect(document.head.querySelector('script')).toBeNull()
})
