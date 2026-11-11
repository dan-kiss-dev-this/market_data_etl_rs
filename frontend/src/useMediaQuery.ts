import { useSyncExternalStore } from 'react'

// Matches the breakpoint where .layout stacks the table above the chart in index.css
export const STACKED = '(max-width: 960px)'

export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const mql = window.matchMedia(query)
      mql.addEventListener('change', onChange)
      return () => mql.removeEventListener('change', onChange)
    },
    () => window.matchMedia(query).matches,
  )
}
