import { queryOptions } from '@tanstack/react-query'
import { api } from './api'

// Ratings change once a day, so anything fetched this session stays good for an hour
const staleTime = 60 * 60 * 1000

export const statusQuery = queryOptions({ queryKey: ['status'], queryFn: () => api.status(), staleTime })

export const sectorsQuery = queryOptions({ queryKey: ['sectors'], queryFn: () => api.sectors(), staleTime })

export const leadersQuery = (sector: string | null) =>
  queryOptions({ queryKey: ['leaders', sector], queryFn: () => api.leaders(sector), staleTime })

export const tickerQuery = (ticker: string) =>
  queryOptions({ queryKey: ['ticker', ticker], queryFn: () => api.ticker(ticker), staleTime })
