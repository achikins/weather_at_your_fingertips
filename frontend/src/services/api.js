const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

export const api = {
  getCities: () => get('/api/cities'),

  getCityWeather: (cityId, year) =>
    get(`/api/weather/city/${cityId}${year ? `?year=${year}` : ''}`),

  getCityMonthly: (cityId, year) =>
    get(`/api/weather/city/${cityId}/monthly${year ? `?year=${year}` : ''}`),

  getCityCurrent: (cityId) =>
    get(`/api/weather/city/${cityId}/current`),

  getHistorical: (cityId, { year, month, day } = {}) => {
    const params = new URLSearchParams({ city_id: cityId })
    if (year && year !== 'all') params.set('year', year)
    if (month && month !== 'all') params.set('month', Number(month) + 1)
    if (day && day !== 'all') params.set('day', day)
    return get(`/api/weather/historical?${params}`)
  },

  getAllAlerts: () => get('/api/alerts/'),

  getCityAlerts: (cityId) => get(`/api/alerts/${cityId}`),
}
