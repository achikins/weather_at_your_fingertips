import { useMemo } from 'react'

export const MONTHS_LIST = [
  { value: 'all', label: 'All Months' },
  { value: '0',  label: 'January' },
  { value: '1',  label: 'February' },
  { value: '2',  label: 'March' },
  { value: '3',  label: 'April' },
  { value: '4',  label: 'May' },
  { value: '5',  label: 'June' },
  { value: '6',  label: 'July' },
  { value: '7',  label: 'August' },
  { value: '8',  label: 'September' },
  { value: '9',  label: 'October' },
  { value: '10', label: 'November' },
  { value: '11', label: 'December' },
]


export const DAYS_LIST = [
  { value: 'all', label: 'All Days' },
  ...Array.from({ length: 31 }, (_, i) => ({
    value: String(i + 1),
    label: String(i + 1),
  })),
]

// Legacy export kept so any other import of SEASONS doesn't break
export const SEASONS = [
  { value: 'all',    label: 'All Months' },
  { value: 'summer', label: 'Summer (Dec – Feb)' },
  { value: 'autumn', label: 'Autumn (Mar – May)' },
  { value: 'winter', label: 'Winter (Jun – Aug)' },
  { value: 'spring', label: 'Spring (Sep – Nov)' },
]

export function useWeatherFilter(monthly, filters) {
  return useMemo(() => {
    if (!monthly || monthly.length === 0) return []

    const { month = 'all', year = 'all', day = 'all' } = filters || {}

    return monthly.filter((m) => {
      if (month !== 'all' && m.monthIndex !== Number(month)) return false

      if (year !== 'all' || day !== 'all') {
        // parse the date field (YYYY-MM-DD)
        const [entryYear, , entryDay] = (m.date || '').split('-')
        if (year !== 'all' && entryYear !== year) return false
        if (day !== 'all' && Number(entryDay) !== Number(day)) return false
      }

      return true
    })
  }, [monthly, filters])
}
