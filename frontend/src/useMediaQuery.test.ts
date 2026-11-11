// @vitest-environment jsdom
/// <reference types="node" />
import { readFileSync } from 'node:fs'
import { act, renderHook } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { STACKED, useMediaQuery } from './useMediaQuery'

// Read from disk: Vitest stubs CSS imports (even ?raw) to empty strings
const css = readFileSync(`${import.meta.dirname}/index.css`, 'utf8')

// jsdom has no matchMedia, so stand in a fake whose match state the test controls
function fakeMatchMedia(initial: boolean) {
  let matches = initial
  const listeners = new Set<() => void>()
  const matchMedia = vi.fn((query: string) => ({
    get matches() {
      return matches
    },
    media: query,
    addEventListener: (_: 'change', cb: () => void) => listeners.add(cb),
    removeEventListener: (_: 'change', cb: () => void) => listeners.delete(cb),
  }))
  vi.stubGlobal('matchMedia', matchMedia)
  return {
    matchMedia,
    listeners,
    resize(next: boolean) {
      matches = next
      listeners.forEach((cb) => cb())
    },
  }
}

afterEach(() => {
  vi.unstubAllGlobals()
})

// App.tsx moves the range picker at STACKED; index.css stacks .layout at its own media query.
// If one changes without the other, the picker moves at a different width than the layout stacks.
test('STACKED matches the media query that stacks .layout in index.css', () => {
  const queries = [...css.matchAll(/@media\s*([^{]+?)\s*\{\s*\.layout\s*\{/g)].map((m) => m[1])
  expect(queries).toEqual([STACKED])
})

test('returns the current match for the query', () => {
  const { matchMedia } = fakeMatchMedia(true)
  const { result } = renderHook(() => useMediaQuery(STACKED))
  expect(result.current).toBe(true)
  expect(matchMedia).toHaveBeenCalledWith(STACKED)
})

test('returns false when the query does not match', () => {
  fakeMatchMedia(false)
  const { result } = renderHook(() => useMediaQuery(STACKED))
  expect(result.current).toBe(false)
})

test('updates when the viewport crosses the breakpoint', () => {
  const media = fakeMatchMedia(false)
  const { result } = renderHook(() => useMediaQuery(STACKED))

  act(() => media.resize(true))
  expect(result.current).toBe(true)

  act(() => media.resize(false))
  expect(result.current).toBe(false)
})

test('stops listening on unmount', () => {
  const media = fakeMatchMedia(false)
  const { unmount } = renderHook(() => useMediaQuery(STACKED))
  expect(media.listeners.size).toBe(1)

  unmount()
  expect(media.listeners.size).toBe(0)
})
