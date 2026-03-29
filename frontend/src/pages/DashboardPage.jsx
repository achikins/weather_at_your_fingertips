import { useState } from 'react'
import { Thermometer, CloudRain, Droplets, Wind } from 'lucide-react'
import CitySelector from '../components/dashboard/CitySelector'
import WeatherCards from '../components/dashboard/WeatherCards'
import { TemperatureChart, RainfallChart, HumidityChart, WindChart } from '../components/charts/WeatherChart'
import { australianCities } from '../data/australianCities'
import { getWeatherForCity } from '../data/mockWeatherData'

function ChartCard({ title, icon: Icon, iconColor, children }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-[#1a2035] p-4 hover:border-white/10 transition-colors animate-fade-in">
      <div className="flex items-center gap-2 mb-4">
        <Icon size={15} className={iconColor} />
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>
      <div className="h-52">{children}</div>
    </div>
  )
}

export default function DashboardPage() {
  const [selectedCity, setSelectedCity] = useState(australianCities[0])
  const [selectedYear, setSelectedYear] = useState('2025')

  const handleCityChange = (cityId) => {
    const city = australianCities.find((c) => c.id === cityId)
    if (city) setSelectedCity(city)
  }

  const years = ['2023', '2024', '2025']

  const weather = getWeatherForCity(selectedCity?.id)
  const monthly = weather?.monthly || []
  const current = weather?.current || null

  return (
    <div className="h-full overflow-y-auto px-4 lg:px-6 py-5 space-y-5 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-white font-semibold text-lg">{selectedCity?.name}</h2>
          <p className="text-slate-400 text-sm">
            {selectedCity?.state} · {selectedCity?.description}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-[#1a2035] px-3 py-2">
            <label className="text-sm text-slate-400">Year:</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="bg-transparent text-white text-sm outline-none"
            >
              {years.map((year) => (
                <option key={year} value={year} className="bg-[#1a2035] text-white">
                  {year}
                </option>
              ))}
            </select>
          </div>

          <CitySelector
            selectedCity={selectedCity}
            onCityChange={handleCityChange}
          />
        </div>
      </div>

      {/* Layout: weather cards left, charts right on large screens */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Weather summary cards */}
        <div className="lg:col-span-1">
          <WeatherCards current={current} monthly={monthly} city={selectedCity} />
        </div>

        {/* Charts */}
        <div className="lg:col-span-2 space-y-4">
          <ChartCard title="Temperature (°C)" icon={Thermometer} iconColor="text-orange-400">
            <TemperatureChart data={monthly} />
          </ChartCard>
          <ChartCard title="Monthly Rainfall (mm)" icon={CloudRain} iconColor="text-blue-400">
            <RainfallChart data={monthly} />
          </ChartCard>
        </div>
      </div>

      {/* Bottom row: humidity and wind */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ChartCard title="Relative Humidity (%)" icon={Droplets} iconColor="text-teal-400">
          <HumidityChart data={monthly} />
        </ChartCard>
        <ChartCard title="Wind Speed (km/h)" icon={Wind} iconColor="text-purple-400">
          <WindChart data={monthly} />
        </ChartCard>
      </div>

      {/* Monthly data table */}
      <div className="rounded-2xl border border-white/5 bg-[#1a2035] overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5">
          <h3 className="text-sm font-medium text-white">Monthly Data Table</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-white/5">
                {['Month', 'Min °C', 'Avg °C', 'Max °C', 'Rainfall mm', 'Humidity %', 'Wind km/h'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-slate-500 font-medium uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {monthly.map((m) => (
                <tr key={m.month} className="hover:bg-white/2 transition-colors">
                  <td className="px-4 py-2.5 text-slate-300 font-medium">{m.month}</td>
                  <td className="px-4 py-2.5 text-blue-400">{m.tempMin}°</td>
                  <td className="px-4 py-2.5 text-teal-400">{m.tempAvg}°</td>
                  <td className="px-4 py-2.5 text-orange-400">{m.tempMax}°</td>
                  <td className="px-4 py-2.5 text-slate-300">{m.rainfall}</td>
                  <td className="px-4 py-2.5 text-slate-300">{m.humidity}%</td>
                  <td className="px-4 py-2.5 text-slate-300">{m.windSpeed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}