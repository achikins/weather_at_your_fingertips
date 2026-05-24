import { useState, useRef, useEffect } from 'react'
import { Calendar, X, ChevronDown } from 'lucide-react'
import { MONTHS_LIST } from '../../hooks/useWeatherFilter'

function PopupSelect({ label, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-medium uppercase tracking-wider text-gray-400 dark:text-slate-500">{label}</span>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10
                     text-gray-700 dark:text-slate-300 text-xs rounded-lg px-3 py-2 pr-7
                     focus:outline-none focus:border-blue-400 dark:focus:border-blue-500/50 cursor-pointer"
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <ChevronDown size={11} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 pointer-events-none" />
      </div>
    </div>
  )
}

export default function WeatherFilter({ filters, onFilterChange, availableYears = [] }) {
  const yearOptions = [
    { value: 'all', label: 'All Years' },
    ...availableYears.map((y) => ({ value: String(y), label: String(y) })),
  ]
  const { month, year } = filters
  const [open, setOpen] = useState(false)
  const popupRef = useRef(null)

  const isFiltered = month !== 'all' || year !== 'all'

  const handleClear = () => {
    onFilterChange({ month: 'all', year: 'all' })
  }

  // Close popup on outside click
  useEffect(() => {
    function handleClick(e) {
      if (popupRef.current && !popupRef.current.contains(e.target)) setOpen(false)
    }
    if (open) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  const activeLabel = () => {
    const parts = []
    if (year !== 'all') parts.push(year)
    if (month !== 'all') parts.push(MONTHS_LIST.find(m => m.value === month)?.label)
    return parts.length ? parts.join(' · ') : 'Date Filter'
  }

  return (
    <div className="flex items-center gap-2">
      {/* Calendar popup trigger */}
      <div className="relative" ref={popupRef}>
        <button
          onClick={() => setOpen((p) => !p)}
          className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm transition-colors shadow-sm dark:shadow-none
            ${isFiltered
              ? 'bg-blue-50 dark:bg-blue-500/10 border-blue-200 dark:border-blue-500/30 text-blue-600 dark:text-blue-400'
              : 'bg-white dark:bg-[#1a2035] border-gray-200 dark:border-white/10 text-gray-700 dark:text-slate-300 hover:border-gray-300 dark:hover:border-white/20'
            }`}
        >
          <Calendar size={14} className={isFiltered ? 'text-blue-500' : 'text-blue-400'} />
          <span>{activeLabel()}</span>
          <ChevronDown size={12} className="text-gray-400 dark:text-slate-500" />
        </button>

        {/* Popup */}
        {open && (
          <div className="absolute top-full mt-2 right-0 z-50 w-64 bg-white dark:bg-[#1a2035] border border-gray-200 dark:border-white/10 rounded-2xl shadow-xl dark:shadow-black/40 p-4 space-y-3">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-gray-900 dark:text-white text-xs font-semibold">
                <Calendar size={13} className="text-blue-400" />
                <span>Date Filter</span>
              </div>
              <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors">
                <X size={13} />
              </button>
            </div>

            <div className="h-px bg-gray-100 dark:bg-white/5" />

            <PopupSelect
              label="Year"
              value={year}
              onChange={(v) => onFilterChange({ ...filters, year: v })}
              options={yearOptions}
            />
            <PopupSelect
              label="Month"
              value={month}
              onChange={(v) => onFilterChange({ ...filters, month: v })}
              options={MONTHS_LIST}
            />
            {/* Clear button */}
            {isFiltered && (
              <button
                onClick={() => { handleClear(); setOpen(false) }}
                className="w-full flex items-center justify-center gap-1.5 py-2 rounded-xl
                           bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/30
                           text-blue-600 dark:text-blue-400 text-xs font-medium
                           hover:bg-blue-100 dark:hover:bg-blue-500/20 transition-colors"
              >
                <X size={11} />
                Clear all filters
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
