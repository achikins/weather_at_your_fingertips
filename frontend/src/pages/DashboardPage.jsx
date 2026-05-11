import { useState, useEffect } from 'react'
import { Thermometer, CloudRain, Droplets, Wind } from 'lucide-react'
import WeatherCards from '../components/dashboard/WeatherCards'
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
  const [availableYears, setAvailableYears] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!selectedCity) return
    setLoading(true)
    setError(null)
    api.getCityWeather(selectedCity.id, filters.year !== 'all' ? filters.year : undefined)
      .then((data) => {
        setMonthly(data.monthly || [])
        setCurrent(data.current || null)
        setAvailableYears(data.available_years || [])
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
        <div>
          <h2 className="text-gray-900 dark:text-white font-semibold text-lg">{selectedCity?.name}</h2>
          <p className="text-gray-500 dark:text-slate-400 text-sm">{selectedCity?.state} · {selectedCity?.description}</p>
        </div>
        <WeatherFilter
          filters={filters}
          onFilterChange={setFilters}
          selectedCity={selectedCity}
          onCityChange={handleCityChange}
          availableYears={availableYears}
        />
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 px-4 py-3 text-sm text-red-600 dark:text-red-400">
          Could not load weather data: {error}
        </div>
      )}

      {/* Summary cards */}
      <WeatherCards monthly={monthly} loading={loading} />

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
