export interface Metrics {
  n: number
  mae: number | null
  rmse: number | null
  bias: number | null
  nmae: number | null
  maxAbsError: number | null
  p10: number | null
  p50: number | null
  p90: number | null
  overForecastShare: number | null
}

export interface Meta {
  decisionDates: string[]
  defaultCutoff: string
  dataFetchedAt: string
  sources: { forecasts?: string; actuals?: string }
  publishRuns: number
}

export interface HourRow {
  time: string
  localHour: string
  forecast: number | null
  actual: number | null
  error: number | null
  publishTime: string | null
  horizonHours: number | null
}

export interface DayView {
  decisionDate: string
  deliveryDate: string
  cutoff: string
  publishTimesUsed: string[]
  hours: HourRow[]
  halfHourlyActuals: { time: string; actual: number | null }[]
  metrics: Metrics
  monthErrorBand: { p10: number | null; p90: number | null }
}

export interface MonthView {
  cutoff: string
  overall: Metrics
  coverage: { hours: number; missingForecast: number; missingActual: number }
}
