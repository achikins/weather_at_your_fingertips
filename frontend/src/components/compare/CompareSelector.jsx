import { MapPin, ChevronDown, ArrowLeftRight } from 'lucide-react'
import { australianCities } from '../../data/australianCities'

export default function CompareSelector({ city1, city2, onCity1Change, onCity2Change, onSwap }) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {/* City 1 */}
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-blue-500 shrink-0" />
        <div className="relative">
          <select
            value={city1?.id || ''}
            onChange={(e) => onCity1Change(e.target.value)}
            className="appearance-none bg-[#1a2035] border border-blue-500/30 text-white text-sm rounded-xl px-4 py-2 pr-9
                       focus:outline-none focus:border-blue-500/60 hover:border-blue-500/50 transition-colors cursor-pointer"
          >
            {australianCities.map((c) => (
              <option key={c.id} value={c.id} className="bg-[#1a2035]">
                {c.name} ({c.stateCode})
              </option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-blue-400 pointer-events-none" />
        </div>
      </div>

      {/* Swap button */}
      <button
        onClick={onSwap}
        className="w-8 h-8 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 flex items-center justify-center transition-all duration-200 hover:rotate-180"
        style={{ transition: 'all 0.3s' }}
        title="Swap cities"
      >
        <ArrowLeftRight size={13} className="text-slate-400" />
      </button>

      {/* City 2 */}
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-teal-400 shrink-0" />
        <div className="relative">
          <select
            value={city2?.id || ''}
            onChange={(e) => onCity2Change(e.target.value)}
            className="appearance-none bg-[#1a2035] border border-teal-500/30 text-white text-sm rounded-xl px-4 py-2 pr-9
                       focus:outline-none focus:border-teal-500/60 hover:border-teal-500/50 transition-colors cursor-pointer"
          >
            {australianCities.map((c) => (
              <option key={c.id} value={c.id} className="bg-[#1a2035]">
                {c.name} ({c.stateCode})
              </option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-teal-400 pointer-events-none" />
        </div>
      </div>
    </div>
  )
}
