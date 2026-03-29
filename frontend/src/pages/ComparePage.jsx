import { useState } from 'react'
import CompareSelector from '../components/compare/CompareSelector'
import CompareCharts from '../components/compare/CompareCharts'
import { australianCities } from '../data/australianCities'

export default function ComparePage() {
  const [city1, setCity1] = useState(australianCities[0]) // Sydney
  const [city2, setCity2] = useState(australianCities[1]) // Melbourne
  const [selectedYear, setSelectedYear] = useState('2025')

  const handleCity1Change = (id) => {
    const c = australianCities.find((x) => x.id === id)
    if (c) setCity1(c)
  }

  const handleCity2Change = (id) => {
    const c = australianCities.find((x) => x.id === id)
    if (c) setCity2(c)
  }

  const handleSwap = () => {
    setCity1(city2)
    setCity2(city1)
  }

  const years = ['2023', '2024', '2025']

  return (
    <div className="h-full overflow-y-auto px-4 lg:px-6 py-5 space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-white font-semibold text-lg">
            {city1.name} vs {city2.name}
          </h2>
          <p className="text-slate-400 text-sm">
            {city1.state} vs {city2.state}
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

          <CompareSelector
            city1={city1}
            city2={city2}
            onCity1Change={handleCity1Change}
            onCity2Change={handleCity2Change}
            onSwap={handleSwap}
          />
        </div>
      </div>

      {/* City info cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { city: city1, color: 'blue', borderColor: 'border-blue-500/25', textColor: 'text-blue-400', dot: 'bg-blue-500' },
          { city: city2, color: 'teal', borderColor: 'border-teal-500/25', textColor: 'text-teal-400', dot: 'bg-teal-400' },
        ].map(({ city, borderColor, textColor, dot }) => (
          <div key={city.id} className={`rounded-2xl border ${borderColor} bg-[#1a2035] px-4 py-3 flex items-start gap-3`}>
            <span className={`w-2.5 h-2.5 rounded-full ${dot} mt-1 shrink-0`} />
            <div>
              <p className={`font-semibold text-sm ${textColor}`}>{city.name}</p>
              <p className="text-xs text-slate-400 mt-0.5">{city.state}</p>
              <p className="text-[11px] text-slate-500 mt-1">{city.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Comparison charts */}
      <CompareCharts city1={city1} city2={city2} />
    </div>
  )
}