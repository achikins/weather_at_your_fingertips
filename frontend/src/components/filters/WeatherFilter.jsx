import { Filter, X, MapPin, Calendar, ChevronDown } from 'lucide-react'
import { australianCities } from '../../data/australianCities'
import { SEASONS } from '../../hooks/useWeatherFilter'

export default function WeatherFilter({ season, onSeasonChange, selectedCity, onCityChange }) {
  const isFiltered = season !== 'all' || (selectedCity && selectedCity.id !== australianCities[0].id)

  const handleClear = () => {
    onSeasonChange('all')
    onCityChange(australianCities[0].id)
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Season */}
      <div className="flex items-center gap-2 bg-white dark:bg-[#1a2035] border border-gray-200 dark:border-white/10 rounded-xl px-3 py-2 hover:border-gray-300 dark:hover:border-white/20 transition-colors shadow-sm dark:shadow-none">
        <Calendar size={14} className="text-blue-500 dark:text-blue-400 shrink-0" />
        <div className="relative">
          <select
            value={season}
            onChange={(e) => onSeasonChange(e.target.value)}
            className="appearance-none bg-transparent text-gray-700 dark:text-slate-300 text-sm pr-6 focus:outline-none cursor-pointer"
          >
            {SEASONS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
          <ChevronDown size={13} className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* City */}
      <div className="flex items-center gap-2 bg-white dark:bg-[#1a2035] border border-gray-200 dark:border-white/10 rounded-xl px-3 py-2 hover:border-gray-300 dark:hover:border-white/20 transition-colors shadow-sm dark:shadow-none">
        <MapPin size={14} className="text-teal-500 dark:text-teal-400 shrink-0" />
        <div className="relative">
          <select
            value={selectedCity?.id || ''}
            onChange={(e) => onCityChange(e.target.value)}
            className="appearance-none bg-transparent text-gray-700 dark:text-slate-300 text-sm pr-6 focus:outline-none cursor-pointer"
          >
            {australianCities.map((city) => (
              <option key={city.id} value={city.id}>{city.name} — {city.stateCode}</option>
            ))}
          </select>
          <ChevronDown size={13} className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* Clear / indicator */}
      {isFiltered ? (
        <button
          onClick={handleClear}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/30
                     text-blue-600 dark:text-blue-400 text-sm hover:bg-blue-100 dark:hover:bg-blue-500/20 transition-colors"
        >
          <X size={13} />
          <span>Clear</span>
        </button>
      ) : (
        <div className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-gray-100 dark:border-white/5 text-gray-400 dark:text-slate-600 text-sm select-none">
          <Filter size={13} />
          <span>Filters</span>
        </div>
      )}
    </div>
  )
}
