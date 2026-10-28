import { longDate } from '../format'

interface Props {
  dates: string[]
  date: string
  onDateChange: (date: string) => void
}

export function DatePicker({ dates, date, onDateChange }: Props) {
  const index = dates.indexOf(date)
  return (
    <div className="date-stepper">
      <button aria-label="Previous day" disabled={index <= 0} onClick={() => onDateChange(dates[index - 1])}>‹</button>
      <select aria-label="Purchase decision day" value={date} onChange={(e) => onDateChange(e.target.value)}>
        {dates.map((d) => <option key={d} value={d}>Decision on {longDate(d)}</option>)}
      </select>
      <button aria-label="Next day" disabled={index >= dates.length - 1} onClick={() => onDateChange(dates[index + 1])}>›</button>
    </div>
  )
}
