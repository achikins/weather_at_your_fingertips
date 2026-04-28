import { Filter, X, MapPin, Calendar, ChevronDown } from 'lucide-react'
import { australianCities } from '../../data/australianCities'
import { SEASONS } from '../../hooks/useWeatherFilter'

/**
 * WeatherFilter — compact inline filter bar for season + city.
 *
 * Props:
 *   season        {string}   current season value ('all' | 'summer' | 'autumn' | 'winter' | 'spring')
 *   onSeasonChange {Function} called with the new season string
 *   selectedCity  {Object}   the full city object currently selected
 *   onCityChange  {Function} called with a city id string (matches DashboardPage handleCityChange)
 */
export default function WeatherFilter({ season, onSeasonChange, selectedCity, onCityChange }) {
  const isFiltered = season !== 'all' || (selectedCity && selectedCity.id !== australianCities[0].id)

  const handleClear = () => {
    onSeasonChange('all')
    onCityChange(australianCities[0].id)
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Season filter */}
      <div className="flex items-center gap-2 bg-[#1a2035] border border-white/10 rounded-xl px-3 py-2 hover:border-white/20 transition-colors">
        <Calendar size={14} className="text-blue-400 shrink-0" />
        <div className="relative">
          <select
            value={season}
            onChange={(e) => onSeasonChange(e.target.value)}
            className="appearance-none bg-transparent text-slate-300 text-sm pr-6 focus:outline-none cursor-pointer"
          >
            {SEASONS.map((s) => (
              <option key={s.value} value={s.value} className="bg-[#1a2035] text-slate-300">
                {s.label}
              </option>
            ))}
          </select>
          <ChevronDown size={13} className="absolute right-0 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* City filter */}
      <div className="flex items-center gap-2 bg-[#1a2035] border border-white/10 rounded-xl px-3 py-2 hover:border-white/20 transition-colors">
        <MapPin size={14} className="text-teal-400 shrink-0" />
        <div className="relative">
          <select
            value={selectedCity?.id || ''}
            onChange={(e) => onCityChange(e.target.value)}
            className="appearance-none bg-transparent text-slate-300 text-sm pr-6 focus:outline-none cursor-pointer"
          >
            {australianCities.map((city) => (
              <option key={city.id} value={city.id} className="bg-[#1a2035] text-slate-300">
                {city.name} — {city.stateCode}
              </option>
            ))}
          </select>
          <ChevronDown size={13} className="absolute right-0 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* Filter active indicator + clear button */}
      {isFiltered ? (
        <button
          onClick={handleClear}
          title="Clear filters"
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-500/10 border border-blue-500/30
                     text-blue-400 text-sm hover:bg-blue-500/20 hover:border-blue-400/50 transition-colors"
        >
          <X size={13} />
          <span>Clear</span>
        </button>
      ) : (
        <div className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-white/5 text-slate-600 text-sm select-none">
          <Filter size={13} />
          <span>Filters</span>
        </div>
      )}
    </div>
  )
}
