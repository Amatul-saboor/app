import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { mw, ukTime } from '../format'
import type { DayView } from '../types'

const axisMw = (v: number) => (v === 0 ? '0' : `${(v / 1000).toFixed(0)}k`)
const tick = { fill: 'var(--muted)', fontSize: 12 }

export function DayChart({ day }: { day: DayView }) {
  const { p10, p90 } = day.monthErrorBand
  const forecastAt = new Map(day.hours.map((h) => [h.time, h.forecast]))

  // One row per half-hour: actuals are half-hourly, forecasts hourly (drawn through the hour points).
  const series = day.halfHourlyActuals.map(({ time, actual }) => {
    const forecast = forecastAt.get(time) ?? null
    // actual = forecast - error, so January's P10..P90 error gives a likely range for the outturn.
    const band = forecast != null && p10 != null && p90 != null ? [forecast - p90, forecast - p10] : null
    return { label: ukTime(time), actual, forecast, band }
  })

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={series} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis dataKey="label" interval={5} tick={tick} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={axisMw} tick={tick} tickLine={false} axisLine={false} width={44}
          label={{ value: 'MW', angle: -90, position: 'insideLeft', fill: 'var(--muted)', fontSize: 12 }} />
        <Tooltip content={<SeriesTooltip />} />
        <Legend wrapperStyle={{ fontSize: 13, paddingTop: 8 }} />
        <Area dataKey="band" name="Likely actual range (based on January's errors)" fill="var(--forecast)"
          fillOpacity={0.12} stroke="none" connectNulls isAnimationActive={false} />
        <Line dataKey="forecast" name="Forecast at decision time" stroke="var(--forecast)" strokeWidth={2.5}
          dot={false} connectNulls isAnimationActive={false} />
        <Line dataKey="actual" name="Actual wind generation" stroke="var(--actual)" strokeWidth={2}
          dot={false} connectNulls={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

interface TooltipProps {
  active?: boolean
  label?: string
  payload?: { payload: { actual: number | null; forecast: number | null; band: number[] | null } }[]
}

function SeriesTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null
  const { actual, forecast, band } = payload[0].payload
  return (
    <div className="tooltip">
      <strong>{label}</strong>
      {forecast != null && <div><span className="dot forecast" />Forecast {mw(forecast)}</div>}
      {actual != null && <div><span className="dot actual" />Actual {mw(actual)}</div>}
      {forecast != null && actual != null && <div className="muted">Difference {mw(forecast - actual, true)}</div>}
      {band && <div className="muted">Likely range {mw(band[0])} – {mw(band[1])}</div>}
    </div>
  )
}
