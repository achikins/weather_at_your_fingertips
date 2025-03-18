import { useState } from 'react'
import { Bell, Filter } from 'lucide-react'
import AlertCard from './AlertCard'
import { weatherAlerts } from '../../data/mockWeatherData'
import { australianCities } from '../../data/australianCities'

const severities = ['all', 'extreme', 'high', 'moderate', 'low']

const severityCounts = severities.slice(1).reduce((acc, s) => {
  acc[s] = weatherAlerts.filter((a) => a.severity === s).length
  return acc
}, {})

export default function AlertsPanel({ compact = false }) {
  const [filterSeverity, setFilterSeverity] = useState('all')
  const [filterCity, setFilterCity] = useState('all')

  const filtered = weatherAlerts.filter((a) => {
    if (filterSeverity !== 'all' && a.severity !== filterSeverity) return false
    if (filterCity !== 'all' && a.cityId !== filterCity) return false
    return true
  })

  const severityColors = {
    all: 'bg-white/10 text-white border-white/20',
    extreme: 'bg-red-500/15 text-red-300 border-red-500/25',
    high: 'bg-orange-500/15 text-orange-300 border-orange-500/25',
    moderate: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/25',
    low: 'bg-blue-500/15 text-blue-300 border-blue-500/25',
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {weatherAlerts.slice(0, 3).map((alert) => (
          <AlertCard key={alert.id} alert={alert} compact />
        ))}
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col gap-4 animate-fade-in">
      {/* Header stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total Alerts', value: weatherAlerts.length, color: 'text-white', bg: 'bg-white/5' },
          { label: 'Extreme', value: severityCounts.extreme, color: 'text-red-400', bg: 'bg-red-500/10' },
          { label: 'High', value: severityCounts.high, color: 'text-orange-400', bg: 'bg-orange-500/10' },
          { label: 'Moderate', value: severityCounts.moderate, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
        ].map(({ label, value, color, bg }) => (
          <div key={label} className={`rounded-2xl ${bg} border border-white/5 px-4 py-3`}>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-1.5 text-slate-400">
          <Filter size={14} />
          <span className="text-xs font-medium">Filter:</span>
        </div>

        {/* Severity filter */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {severities.map((s) => (
            <button
              key={s}
              onClick={() => setFilterSeverity(s)}
              className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-all capitalize
                ${filterSeverity === s ? severityColors[s] : 'border-white/10 text-slate-500 hover:text-slate-300 hover:border-white/20'}`}
            >
              {s === 'all' ? 'All Levels' : s}
              {s !== 'all' && severityCounts[s] > 0 && (
                <span className="ml-1 opacity-70">({severityCounts[s]})</span>
              )}
            </button>
          ))}
        </div>

        {/* City filter */}
        <select
          value={filterCity}
          onChange={(e) => setFilterCity(e.target.value)}
          className="text-xs bg-[#1a2035] border border-white/10 text-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500/40"
        >
          <option value="all">All Cities</option>
          {australianCities.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {/* Alert list */}
      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-600">
            <Bell size={40} className="mb-3 opacity-50" />
            <p className="text-sm">No alerts match your filters</p>
          </div>
        ) : (
          filtered.map((alert) => <AlertCard key={alert.id} alert={alert} />)
        )}
      </div>
    </div>
  )
}
