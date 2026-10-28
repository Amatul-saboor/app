const UK = 'Europe/London'

const mwFormat = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 })

export function mw(value: number | null | undefined, signed = false): string {
  if (value == null) return '–'
  const text = `${mwFormat.format(Math.abs(value))} MW`
  if (!signed) return value < 0 ? `−${text}` : text
  return value > 0 ? `+${text}` : value < 0 ? `−${text}` : text
}

export function pct(value: number | null | undefined): string {
  return value == null ? '–' : `${(value * 100).toFixed(1)}%`
}

export function ukDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-GB', {
    timeZone: UK, weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

export function ukTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-GB', { timeZone: UK, hour: '2-digit', minute: '2-digit' })
}

/** Formats a plain YYYY-MM-DD date without timezone shifting. */
export function longDate(isoDate: string): string {
  const [y, m, d] = isoDate.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('en-GB', {
    timeZone: 'UTC', weekday: 'short', day: 'numeric', month: 'short',
  })
}
