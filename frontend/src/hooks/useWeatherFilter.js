import { useMemo } from 'react'

export const SEASONS = [
  { value: 'all',    label: 'All Months' },
  { value: 'summer', label: 'Summer (Dec – Feb)' },
  { value: 'autumn', label: 'Autumn (Mar – May)' },
  { value: 'winter', label: 'Winter (Jun – Aug)' },
  { value: 'spring', label: 'Spring (Sep – Nov)' },
]

const SEASON_MONTHS = {
  summer: [11, 0, 1],
  autumn: [2, 3, 4],
  winter: [5, 6, 7],
  spring: [8, 9, 10],
}

export function useWeatherFilter(monthly, season) {
  return useMemo(() => {
    if (!monthly || monthly.length === 0) return []
    if (!season || season === 'all') return monthly
    const allowed = SEASON_MONTHS[season]
    if (!allowed) return monthly
    return monthly.filter((m) => allowed.includes(m.monthIndex))
  }, [monthly, season])
}
