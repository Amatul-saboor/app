import type { DayView, Meta, MonthView } from './types'

async function getJson<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const query = new URLSearchParams(params).toString()
  const response = await fetch(`/api/${path}${query ? `?${query}` : ''}`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed (${response.status})`)
  }
  return response.json()
}

export const fetchMeta = () => getJson<Meta>('meta')
export const fetchDay = (date: string, cutoff: string) => getJson<DayView>('day', { date, cutoff })
export const fetchSummary = (cutoff: string) => getJson<MonthView>('summary', { cutoff })
