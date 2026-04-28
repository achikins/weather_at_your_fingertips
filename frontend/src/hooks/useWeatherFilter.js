export const SEASONS = [
  { value: 'all',    label: 'All Months' },
  { value: 'summer', label: 'Summer (Dec – Feb)' },
  { value: 'autumn', label: 'Autumn (Mar – May)' },
  { value: 'winter', label: 'Winter (Jun – Aug)' },
  { value: 'spring', label: 'Spring (Sep – Nov)' },
]

// monthIndex ranges for each southern-hemisphere season
const SEASON_MONTHS = {
  summer: [11, 0, 1],
  autumn: [2, 3, 4],
  winter: [5, 6, 7],
  spring: [8, 9, 10],
}

/**
 * Filters a 12-entry monthly data array by season.
 *
 * @param {Object[]} monthly - Array of monthly objects with a `monthIndex` field (0 = Jan … 11 = Dec).
 * @param {string}   season  - One of: 'all' | 'summer' | 'autumn' | 'winter' | 'spring'
 * @returns {Object[]} filteredMonthly
 */
export function useWeatherFilter(monthly, season) {
  if (!monthly || monthly.length === 0) return []
  if (!season || season === 'all') return monthly

  const allowed = SEASON_MONTHS[season]
  if (!allowed) return monthly

  // Preserve the natural calendar order that comes from the source data (Jan→Dec),
  // but only include months that belong to the selected season.
  return monthly.filter((m) => allowed.includes(m.monthIndex))
}
