import { useState } from 'react'
import { AlertTriangle, Bell, X } from 'lucide-react'
import { weatherAlerts } from '../../data/mockWeatherData'

// Pick the most severe active alert: first extreme, else first high
const getMostSevereAlert = () => {
  const extreme = weatherAlerts.find((a) => a.severity === 'extreme')
  if (extreme) return extreme
  return weatherAlerts.find((a) => a.severity === 'high') || null
}

export default function AlertBanner({ onViewDetails }) {
  const [dismissed, setDismissed] = useState(false)
  const alert = getMostSevereAlert()

  if (dismissed || !alert) return null

  const isExtreme = alert.severity === 'extreme'

  const containerClass = isExtreme
    ? 'bg-red-500/10 border border-red-500/20'
    : 'bg-orange-500/10 border border-orange-500/20'

  const dotClass = isExtreme ? 'bg-red-500' : 'bg-orange-500'

  const titleClass = isExtreme ? 'text-red-300' : 'text-orange-300'

  const buttonClass = isExtreme
    ? 'text-xs font-semibold px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 hover:bg-red-500/30 transition-colors duration-150'
    : 'text-xs font-semibold px-3 py-1.5 rounded-lg bg-orange-500/20 border border-orange-500/30 text-orange-300 hover:bg-orange-500/30 transition-colors duration-150'

  return (
    <div className={`rounded-xl px-4 py-3 flex items-center justify-between gap-3 ${containerClass}`}>
      {/* Left: indicator + text */}
      <div className="flex items-center gap-3 min-w-0">
        <span className={`w-2.5 h-2.5 rounded-full shrink-0 animate-pulse ${dotClass}`} />
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <AlertTriangle size={13} className={isExtreme ? 'text-red-400 shrink-0' : 'text-orange-400 shrink-0'} />
            <span className={`text-sm font-semibold truncate ${titleClass}`}>{alert.title}</span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 truncate">{alert.cityName} · {alert.type}</p>
        </div>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => onViewDetails && onViewDetails(alert)}
          className={buttonClass}
        >
          <span className="flex items-center gap-1.5">
            <Bell size={11} />
            View Details
          </span>
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors duration-150"
          aria-label="Dismiss alert banner"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  )
}
