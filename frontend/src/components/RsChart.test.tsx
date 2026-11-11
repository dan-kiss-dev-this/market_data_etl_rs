// @vitest-environment jsdom
import { cleanup, fireEvent, render } from '@testing-library/react'
import { Line, LineChart, XAxis, YAxis } from 'recharts'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import type { TickerDetail } from '../api'
import RsChart, { ChartSkeleton, Crosshair } from './RsChart'

// Vitest doesn't expose afterEach globally here, so RTL can't clean up on its own
afterEach(cleanup)

// jsdom has no layout: give every element a 400px-wide box at the page origin,
// so ResponsiveContainer renders and the mouse y equals clientY
beforeEach(() => {
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      disconnect() {}
    },
  )
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue(
    { x: 0, y: 0, top: 0, left: 0, right: 400, bottom: 0, width: 400, height: 0 } as DOMRect,
  )
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

// Plot area is x 52..400, y 0..200, with 0 at the bottom and 100 at the top
function renderCrosshair(y: number | null) {
  const { container } = render(
    <LineChart width={400} height={200} data={[{ v: 0 }, { v: 100 }]} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
      <XAxis hide />
      <YAxis domain={[0, 100]} width={52} />
      {/* The y scale only exists once the chart has a series */}
      <Line dataKey="v" isAnimationActive={false} />
      <Crosshair y={y} format={(v) => v.toFixed(0)} />
    </LineChart>,
  )
  return container
}

test('draws a solid white line across the plot area at the mouse y', () => {
  const line = renderCrosshair(50).querySelector('.crosshair line')!

  expect(line.getAttribute('x1')).toBe('52')
  expect(line.getAttribute('x2')).toBe('400')
  expect(line.getAttribute('y1')).toBe('50')
  expect(line.getAttribute('y2')).toBe('50')
  expect(line.getAttribute('stroke')).toBe('#ffffff')
  expect(line.getAttribute('stroke-width')).toBe('1')
  expect(line.hasAttribute('stroke-dasharray')).toBe(false)
})

test('the y-axis pill shows the value under the mouse, formatted', () => {
  expect(renderCrosshair(50).querySelector('.crosshair-label')?.textContent).toBe('75')
})

test.each([
  ['the mouse is off the chart', null],
  ['the mouse is above the plot area', -1],
  ['the mouse is below the plot area', 201],
])('draws nothing when %s', (_, y) => {
  expect(renderCrosshair(y).querySelector('.crosshair')).toBeNull()
})

const detail: TickerDetail = {
  ticker: 'MRNA',
  name: 'Moderna',
  sector: 'Health Care',
  series: Array.from({ length: 30 }, (_, i) => ({
    date: `2026-01-${String(i + 1).padStart(2, '0')}`,
    close: 100 + i,
    rs_line: 1 + i / 100,
    rs_rating: 50 + i,
  })),
}

test('hovering a panel shows the crosshair in that panel only, and leaving removes it', () => {
  const { container } = render(<RsChart detail={detail} range="3M" benchmark="SPY" stale={false} />)
  const panels = [...container.querySelectorAll('figure.panel')]
  const rating = panels[2].querySelector(':scope > div')!

  fireEvent.mouseMove(rating, { clientY: 64 })
  expect(panels.map((p) => p.querySelector('.crosshair') !== null)).toEqual([false, false, true])
  // RS Rating's plot area is y 8..120 for a 0..100 domain, so y 64 is halfway
  expect(panels[2].querySelector('.crosshair-label')?.textContent).toBe('50')

  fireEvent.mouseLeave(rating)
  expect(container.querySelector('.crosshair')).toBeNull()
})

test('the chart skeleton has one panel per chart, at the chart heights', () => {
  const { container } = render(<ChartSkeleton />)
  const skeletons = [...container.querySelectorAll<HTMLElement>('figure.panel .skeleton-panel')]

  expect(skeletons.map((s) => s.style.height)).toEqual(['180px', '150px', '150px'])
  expect(container.querySelector('section')?.getAttribute('aria-busy')).toBe('true')
})

test('each skeleton panel shows a lightning bolt, taller than it is wide', () => {
  const { container } = render(<ChartSkeleton />)
  const bolts = [...container.querySelectorAll('.skeleton-panel > svg.skeleton-bolt')]

  expect(bolts).toHaveLength(3)
  for (const bolt of bolts) {
    expect(Number(bolt.getAttribute('height'))).toBeGreaterThan(Number(bolt.getAttribute('width')))
    expect(bolt.querySelector('path')).not.toBeNull()
  }
})

test('a stale chart stays drawn, dimmed and marked busy', () => {
  const { container } = render(<RsChart detail={detail} range="3M" benchmark="SPY" stale />)
  const card = container.querySelector('section.chart-card')!

  expect(card.classList.contains('is-loading')).toBe(true)
  expect(card.getAttribute('aria-busy')).toBe('true')
  expect(container.querySelectorAll('.recharts-wrapper')).toHaveLength(3)
})
