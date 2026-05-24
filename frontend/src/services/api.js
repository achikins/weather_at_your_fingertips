import { getWeatherForCity, getAlertsForCity, weatherAlerts } from '../data/mockWeatherData'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

// Wraps a live API call with a mock fallback if the API returns an error
async function withMockFallback(apiFn, mockFn) {
  try {
    return await apiFn()
  } catch (err) {
    console.warn('[api] falling back to mock', err.message)
    return mockFn()
  }
}

export const api = {
  getCities: () => get('/api/cities'),

  getCityWeather: (cityId, year) =>
    withMockFallback(
      () => get(`/api/weather/city/${cityId}${year ? `?year=${year}` : ''}`),
      () => getWeatherForCity(cityId) || { monthly: [], current: null }
    ),

  getCityMonthly: (cityId, year) =>
    withMockFallback(
      () => get(`/api/weather/city/${cityId}/monthly${year ? `?year=${year}` : ''}`),
      () => ({ monthly: getWeatherForCity(cityId)?.monthly || [] })
    ),

  getCityCurrent: (cityId) =>
    withMockFallback(
      () => get(`/api/weather/city/${cityId}/current`),
      () => ({ current: getWeatherForCity(cityId)?.current || null })
    ),
    
  getCitiesSummary: (year) =>
    withMockFallback(
      () => get(`/api/weather/cities/summary${year ? `?year=${year}` : ''}`),
      () => ({ summary: [] })
    ),

  getHistorical: (cityId, { year, month, day } = {}) => {
    const params = new URLSearchParams({ city_id: cityId })
    if (year && year !== 'all') params.set('year', year)
    if (month && month !== 'all') params.set('month', Number(month) + 1)
    if (day && day !== 'all') params.set('day', day)
    return withMockFallback(
      () => get(`/api/weather/historical?${params}`),
      () => ({ historical: getWeatherForCity(cityId)?.monthly || [] })
    )
  },

  getAllAlerts: ({ includeInactive = false } = {}) =>
    withMockFallback(
      () => get(`/api/alerts/${includeInactive ? '?include_inactive=true' : ''}`),
      () => ({ alerts: weatherAlerts })
    ),

  getCityAlerts: (cityId, { includeInactive = false } = {}) =>
    withMockFallback(
      () => get(`/api/alerts/${cityId}${includeInactive ? '?include_inactive=true' : ''}`),
      () => ({ alerts: getAlertsForCity(cityId) })
    ),
}
