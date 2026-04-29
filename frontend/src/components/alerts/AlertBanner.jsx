import { useState } from 'react'
import { AlertTriangle, Bell, X } from 'lucide-react'
import { weatherAlerts } from '../../data/mockWeatherData'

const getMostSevereAlert = () =>
  weatherAlerts.find((a) => a.severity === 'extreme') ||
  weatherAlerts.find((a) => a.severity === 'high') ||
  null

export default function AlertBanner({ onViewDetails }) {
  const [dismissed, setDismissed] = useState(false)
  const alert = getMostSevereAlert()

  if (dismissed || !alert) return null

  const isExtreme = alert.severity === 'extreme'

  const container = isExtreme
    ? 'bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20'
    : 'bg-orange-50 dark:bg-orange-500/10 border border-orange-200 dark:border-orange-500/20'
  const dot  = isExtreme ? 'bg-red-500' : 'bg-orange-500'
  const icon = isExtreme ? 'text-red-500 dark:text-red-400' : 'text-orange-500 dark:text-orange-400'
  const title = isExtreme ? 'text-red-700 dark:text-red-300' : 'text-orange-700 dark:text-orange-300'
  const btn  = isExtreme
    ? 'bg-red-100 dark:bg-red-500/20 border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-500/30'
    : 'bg-orange-100 dark:bg-orange-500/20 border border-orange-200 dark:border-orange-500/30 text-orange-600 dark:text-orange-300 hover:bg-orange-200 dark:hover:bg-orange-500/30'

  return (
    <div className={`rounded-xl px-4 py-3 flex items-center justify-between gap-3 ${container}`}>
      <div className="flex items-center gap-3 min-w-0">
        <span className={`w-2.5 h-2.5 rounded-full shrink-0 animate-pulse ${dot}`} />
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <AlertTriangle size={13} className={`${icon} shrink-0`} />
            <span className={`text-sm font-semibold truncate ${title}`}>{alert.title}</span>
          </div>
          <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5 truncate">{alert.cityName} · {alert.type}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => onViewDetails && onViewDetails(alert)}
          className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors duration-150 ${btn}`}
        >
          <span className="flex items-center gap-1.5">
            <Bell size={11} />
            View Details
          </span>
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="p-1.5 rounded-lg text-gray-400 dark:text-slate-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/10 transition-colors duration-150"
          aria-label="Dismiss alert banner"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  )
}
