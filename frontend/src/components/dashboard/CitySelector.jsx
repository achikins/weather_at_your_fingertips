import { MapPin, ChevronDown } from 'lucide-react'
import { australianCities } from '../../data/australianCities'

export default function CitySelector({ selectedCity, onCityChange }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 text-gray-400 dark:text-slate-400">
        <MapPin size={15} />
        <span className="text-sm font-medium">City:</span>
      </div>
      <div className="relative">
        <select
          value={selectedCity?.id || ''}
          onChange={(e) => onCityChange(e.target.value)}
          className="appearance-none bg-white dark:bg-[#1a2035] border border-gray-200 dark:border-white/10 text-gray-900 dark:text-white text-sm rounded-xl px-4 py-2 pr-9
                     focus:outline-none focus:border-blue-400 dark:focus:border-blue-500/50
                     hover:border-gray-300 dark:hover:border-white/20 transition-colors cursor-pointer shadow-sm dark:shadow-none"
        >
          {australianCities.map((city) => (
            <option key={city.id} value={city.id}>
              {city.name} ({city.stateCode})
            </option>
          ))}
        </select>
        <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-400 pointer-events-none" />
      </div>
    </div>
  )
}
