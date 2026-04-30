import { Filter, X, MapPin, Calendar, CalendarDays, ChevronDown } from 'lucide-react'
import { australianCities } from '../../data/australianCities'
import { MONTHS_LIST, YEARS_LIST, DAYS_LIST } from '../../hooks/useWeatherFilter'

function SelectDropdown({ icon: Icon, iconClass, value, onChange, options }) {
  return (
    <div className="flex items-center gap-2 bg-white dark:bg-[#1a2035] border border-gray-200 dark:border-white/10 rounded-xl px-3 py-2 hover:border-gray-300 dark:hover:border-white/20 transition-colors shadow-sm dark:shadow-none">
      <Icon size={14} className={`${iconClass} shrink-0`} />
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="appearance-none bg-transparent text-gray-700 dark:text-slate-300 text-sm pr-6 focus:outline-none cursor-pointer"
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <ChevronDown size={13} className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-400 pointer-events-none" />
      </div>
    </div>
  )
}

export default function WeatherFilter({ filters, onFilterChange, selectedCity, onCityChange }) {
  const { month, year, day } = filters

  const isFiltered =
    month !== 'all' ||
    year !== 'all' ||
    day !== 'all' ||
    (selectedCity && selectedCity.id !== australianCities[0].id)

  const handleClear = () => {
    onFilterChange({ month: 'all', year: 'all', day: 'all' })
    onCityChange(australianCities[0].id)
  }

  const cityOptions = australianCities.map((c) => ({ value: c.id, label: `${c.name} — ${c.stateCode}` }))

  return (
    <div className="flex flex-wrap items-center gap-2">
      <SelectDropdown
        icon={Calendar}
        iconClass="text-violet-500 dark:text-violet-400"
        value={year}
        onChange={(v) => onFilterChange({ ...filters, year: v })}
        options={YEARS_LIST}
      />

      <SelectDropdown
        icon={Calendar}
        iconClass="text-blue-500 dark:text-blue-400"
        value={month}
        onChange={(v) => onFilterChange({ ...filters, month: v })}
        options={MONTHS_LIST}
      />

      <SelectDropdown
        icon={CalendarDays}
        iconClass="text-orange-500 dark:text-orange-400"
        value={day}
        onChange={(v) => onFilterChange({ ...filters, day: v })}
        options={DAYS_LIST}
      />

      <SelectDropdown
        icon={MapPin}
        iconClass="text-teal-500 dark:text-teal-400"
        value={selectedCity?.id || ''}
        onChange={onCityChange}
        options={cityOptions}
      />

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
