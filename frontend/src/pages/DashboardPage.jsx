import { useState, useEffect } from 'react'
import { Thermometer, CloudRain, Droplets, Wind, MapPin, ChevronDown } from 'lucide-react'
import WeatherCards from '../components/dashboard/WeatherCards'
import Forecast from '../components/dashboard/Forecast'
import { TemperatureChart, RainfallChart, HumidityChart, WindChart } from '../components/charts/WeatherChart'
import ChartCard from '../components/charts/ChartCard'
import { australianCities, getCityById } from '../data/australianCities'
import WeatherFilter from '../components/filters/WeatherFilter'
import { useWeatherFilter } from '../hooks/useWeatherFilter'
import { api } from '../services/api'

export default function DashboardPage() {
  const [selectedCity, setSelectedCity] = useState(australianCities[0])
  const [filters, setFilters] = useState({ month: 'all', year: 'all' })
  const [monthly, setMonthly] = useState([])
  const [current, setCurrent] = useState(null)
  const [forecast, setForecast] = useState([])
  const [availableYears, setAvailableYears] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!selectedCity) return
    setLoading(true)
    setError(null)
    Promise.all([
      api.getCityWeather(selectedCity.id, filters.year !== 'all' ? filters.year : undefined),
      api.getCityForecast(selectedCity.id),
    ])
      .then(([weatherData, forecastData]) => {
        setMonthly(weatherData.monthly || [])
        setCurrent(weatherData.current || null)
        setAvailableYears(weatherData.available_years || [])
        setForecast(forecastData.forecast || [])
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedCity, filters.year])

  const handleCityChange = (cityId) => {
    const city = getCityById(cityId)
    if (city) setSelectedCity(city)
  }

  const filteredMonthly = useWeatherFilter(monthly, filters)

  return (
    <div className="h-full overflow-y-auto px-4 lg:px-6 py-5 space-y-4 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {/* City selector */}
          <div className="relative">
            <div className="flex items-center gap-1.5 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
              <MapPin size={14} className="text-teal-400" />
            </div>
            <select
              value={selectedCity?.id || ''}
              onChange={(e) => handleCityChange(e.target.value)}
              className="appearance-none pl-8 pr-8 py-2 rounded-xl border bg-white dark:bg-[#1a2035]
                         border-gray-200 dark:border-white/10 text-gray-900 dark:text-white
                         text-sm font-semibold cursor-pointer focus:outline-none
                         focus:border-teal-400 dark:focus:border-teal-500/50
                         hover:border-gray-300 dark:hover:border-white/20 transition-colors"
            >
              {australianCities.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 pointer-events-none" />
          </div>
          <p className="text-gray-500 dark:text-slate-400 text-sm hidden sm:block">{selectedCity?.state} · {selectedCity?.description}</p>
        </div>
        <WeatherFilter
          filters={filters}
          onFilterChange={setFilters}
          availableYears={availableYears}
        />
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 px-4 py-3 text-sm text-red-600 dark:text-red-400">
          Could not load weather data: {error}
        </div>
      )}

      {/* Summary cards */}
      <WeatherCards monthly={monthly} current={current} loading={loading} />

      <Forecast
        forecast={forecast}
        currentDate={current?.obsDate || null}
        loading={loading}
      />

      {loading && !monthly.length && (
        <div className="text-sm text-gray-400 dark:text-slate-500 text-center py-6">Loading weather data…</div>
      )}

      {/* Charts: 2-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Temperature (°C)" icon={Thermometer} iconColor="text-orange-400" data={filteredMonthly}>
          <TemperatureChart data={filteredMonthly} />
        </ChartCard>
        <ChartCard title="Monthly Rainfall (mm)" icon={CloudRain} iconColor="text-blue-400" data={filteredMonthly}>
          <RainfallChart data={filteredMonthly} />
        </ChartCard>
        <ChartCard title="Relative Humidity (%)" icon={Droplets} iconColor="text-teal-400" data={filteredMonthly}>
          <HumidityChart data={filteredMonthly} />
        </ChartCard>
        <ChartCard title="Wind Speed (km/h)" icon={Wind} iconColor="text-purple-400" data={filteredMonthly}>
          <WindChart data={filteredMonthly} />
        </ChartCard>
      </div>

      {/* Monthly data table */}
      <div className="rounded-2xl border border-gray-100 dark:border-white/5 bg-white dark:bg-[#1a2035] overflow-hidden shadow-sm dark:shadow-none">
        <div className="px-5 py-3 border-b border-gray-100 dark:border-white/5">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">Monthly Data Table</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100 dark:border-white/5">
                {['Month', 'Date', 'Min °C', 'Avg °C', 'Max °C', 'Rainfall mm', 'Humidity %', 'Wind km/h'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-gray-400 dark:text-slate-500 font-medium uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-white/5">
              {filteredMonthly.map((m) => (
                <tr key={m.month} className="hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-2.5 text-gray-700 dark:text-slate-300 font-medium">{m.month}</td>
                  <td className="px-4 py-2.5 text-gray-400 dark:text-slate-500">{m.date}</td>
                  <td className="px-4 py-2.5 text-blue-500 dark:text-blue-400">{m.tempMin}°</td>
                  <td className="px-4 py-2.5 text-teal-500 dark:text-teal-400">{m.tempAvg}°</td>
                  <td className="px-4 py-2.5 text-orange-500 dark:text-orange-400">{m.tempMax}°</td>
                  <td className="px-4 py-2.5 text-gray-600 dark:text-slate-300">{m.rainfall}</td>
                  <td className="px-4 py-2.5 text-gray-600 dark:text-slate-300">{m.humidity}%</td>
                  <td className="px-4 py-2.5 text-gray-600 dark:text-slate-300">{m.windSpeed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
