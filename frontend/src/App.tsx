import { useEffect, useState } from 'react'
import { fetchDay, fetchMeta, fetchSummary } from './api'
import { DatePicker } from './components/DatePicker'
import { DayChart } from './components/DayChart'
import { longDate, mw, pct, ukDateTime } from './format'
import type { DayView, Meta, MonthView } from './types'

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [date, setDate] = useState('')
  const [day, setDay] = useState<DayView | null>(null)
  const [month, setMonth] = useState<MonthView | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchMeta()
      .then((m) => {
        setMeta(m)
        setDate(m.decisionDates[Math.floor(m.decisionDates.length / 2)])
        return fetchSummary(m.defaultCutoff)
      })
      .then(setMonth)
      .catch((e: Error) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!meta || !date) return
    let stale = false
    fetchDay(date, meta.defaultCutoff)
      .then((d) => !stale && setDay(d))
      .catch((e: Error) => !stale && setError(e.message))
    return () => { stale = true }
  }, [meta, date])

  if (error) return <main className="page"><div className="card error">Could not load data: {error}</div></main>
  if (!meta || !day || !month) return <main className="page"><div className="loading">Loading Elexon data…</div></main>

  const overall = month.overall
  const dayBias = day.metrics.bias

  return (
    <main className="page">
      <header>
        <h1>Wind Forecast Accuracy</h1>
        <p className="muted">GB national wind generation · day-ahead purchase decisions in January 2026</p>
      </header>

      <section className="card">
        <div className="section-head">
          <div>
            <h2>What wind did the forecast promise?</h2>
            <p className="muted">
              Decision on {longDate(day.decisionDate)} at {day.cutoff} (day-ahead auction close) for delivery on{' '}
              {longDate(day.deliveryDate)}
            </p>
          </div>
          <DatePicker dates={meta.decisionDates} date={date} onDateChange={setDate} />
        </div>
        <p className="forecast-used">
          {day.publishTimesUsed.length
            ? <>Forecast used: published <strong>{day.publishTimesUsed.map(ukDateTime).join(', ')}</strong>, the latest available before {day.cutoff}.</>
            : `No forecast had been published before ${day.cutoff}.`}
        </p>
        <DayChart day={day} />
        {dayBias != null && (
          <p className="day-summary">
            For this day the forecast was on average <strong>{mw(Math.abs(dayBias))} too {dayBias > 0 ? 'high' : 'low'}</strong>
            {day.metrics.maxAbsError != null && <>, missing by up to {mw(day.metrics.maxAbsError)} in a single hour</>}.
          </p>
        )}
      </section>

      <section className="card">
        <h2>How far can the forecast be trusted?</h2>
        <p className="muted">
          All {overall.n} delivery hours for decisions made 1–31 January, using the forecast available at {month.cutoff} each day.
        </p>
        <div className="metrics-row">
          <Metric label="Typical miss (MAE)" value={mw(overall.mae)} hint={`${pct(overall.nmae)} of average wind output`} />
          <Metric label="Bias" value={mw(overall.bias, true)} hint={`too high in ${pct(overall.overForecastShare)} of hours`} warn />
          <Metric label="Safety margin (P90)" value={mw(overall.p90)} hint="covers the shortfall in 9 of 10 hours" warn />
          <Metric label="RMSE" value={mw(overall.rmse)} hint="weights large misses more" />
        </div>
        <p className="insight">
          <strong>What this means for buying:</strong> the forecast usually promised more wind than arrived. To be
          covered in 9 out of 10 hours, plan for about <strong>{mw(overall.p90)} less wind</strong> than the forecast shows.
        </p>
      </section>

      <footer className="muted small">
        Data: Elexon <a href={meta.sources.forecasts} target="_blank" rel="noreferrer">WINDFOR</a> (forecasts) and{' '}
        <a href={meta.sources.actuals} target="_blank" rel="noreferrer">FUELHH</a> (actual wind) · error = forecast − actual.
      </footer>
    </main>
  )
}

function Metric({ label, value, hint, warn = false }: { label: string; value: string; hint: string; warn?: boolean }) {
  return (
    <div className={`metric ${warn ? 'warn' : ''}`}>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-hint">{hint}</div>
    </div>
  )
}
