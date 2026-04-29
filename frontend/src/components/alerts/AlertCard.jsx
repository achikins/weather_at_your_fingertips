import { useState } from 'react'
import { AlertTriangle, CloudLightning, Droplets, Wind, Waves, Thermometer, Clock, MapPin, ShieldCheck } from 'lucide-react'

const typeIcons = {
  'Severe Storm':   CloudLightning,
  'Heavy Rainfall': Droplets,
  'Heatwave':       Thermometer,
  'Strong Winds':   Wind,
  'Coastal Hazard': Waves,
  'Thunderstorm':   CloudLightning,
}

const severityConfig = {
  extreme: {
    badge:   'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-300 border-red-200 dark:border-red-500/30',
    border:  'border-l-red-500',
    icon:    'text-red-500 dark:text-red-400',
    iconBg:  'bg-red-50 dark:bg-red-500/10',
    label:   'EXTREME',
    dot:     'bg-red-500',
  },
  high: {
    badge:   'bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-300 border-orange-200 dark:border-orange-500/30',
    border:  'border-l-orange-500',
    icon:    'text-orange-500 dark:text-orange-400',
    iconBg:  'bg-orange-50 dark:bg-orange-500/10',
    label:   'HIGH',
    dot:     'bg-orange-500',
  },
  moderate: {
    badge:   'bg-yellow-100 dark:bg-yellow-500/20 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-500/30',
    border:  'border-l-yellow-400',
    icon:    'text-yellow-600 dark:text-yellow-400',
    iconBg:  'bg-yellow-50 dark:bg-yellow-500/10',
    label:   'MODERATE',
    dot:     'bg-yellow-400',
  },
  low: {
    badge:   'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-300 border-blue-200 dark:border-blue-500/30',
    border:  'border-l-blue-400',
    icon:    'text-blue-500 dark:text-blue-400',
    iconBg:  'bg-blue-50 dark:bg-blue-500/10',
    label:   'LOW',
    dot:     'bg-blue-400',
  },
}

const formatTime = (isoString) =>
  new Date(isoString).toLocaleString('en-AU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

const timeUntilExpiry = (isoString) => {
  const diff = new Date(isoString) - new Date()
  if (diff < 0) return 'Expired'
  const hours = Math.floor(diff / 3600000)
  if (hours < 24) return `Expires in ${hours}h`
  return `Expires in ${Math.floor(hours / 24)}d ${hours % 24}h`
}

export default function AlertCard({ alert, compact = false }) {
  const [tipsOpen, setTipsOpen] = useState(false)
  const config = severityConfig[alert.severity] || severityConfig.low
  const Icon   = typeIcons[alert.type] || AlertTriangle

  if (compact) {
    return (
      <div className={`flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white dark:bg-[#1a2035] border border-gray-100 dark:border-white/5 border-l-2 ${config.border} hover:border-gray-200 dark:hover:border-white/10 transition-all duration-200`}>
        <span className={`w-2 h-2 rounded-full shrink-0 ${config.dot} animate-pulse`} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold text-gray-900 dark:text-white truncate">{alert.title}</p>
            <span className={`hidden sm:inline-flex shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded border ${config.badge}`}>
              {config.label}
            </span>
          </div>
          <p className="text-[10px] text-gray-400 dark:text-slate-500">{alert.cityName} · {alert.type}</p>
        </div>
        <span className="text-[10px] text-gray-400 dark:text-slate-500 shrink-0">{timeUntilExpiry(alert.expires)}</span>
      </div>
    )
  }

  return (
    <div className={`rounded-2xl bg-white dark:bg-[#1a2035] border border-gray-100 dark:border-white/5 border-l-4 ${config.border} overflow-hidden hover:border-gray-200 dark:hover:border-white/10 transition-all duration-200 animate-fade-in shadow-sm dark:shadow-none`}>
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-start gap-3">
          <div className={`w-10 h-10 rounded-xl ${config.iconBg} flex items-center justify-center shrink-0 mt-0.5`}>
            <Icon size={18} className={config.icon} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start gap-2 flex-wrap">
              <h3 className="text-gray-900 dark:text-white font-semibold text-sm leading-tight">{alert.title}</h3>
              <span className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full border ${config.badge}`}>{config.label}</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <MapPin size={11} className="text-gray-400 dark:text-slate-500" />
              <p className="text-xs text-gray-500 dark:text-slate-400">{alert.cityName} · {alert.type}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="px-5 pb-3">
        <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed">{alert.description}</p>
      </div>

      {alert.affectedAreas?.length > 0 && (
        <div className="px-5 pb-3">
          <p className="text-[10px] text-gray-400 dark:text-slate-500 font-medium uppercase tracking-wider mb-2">Affected Areas</p>
          <div className="flex flex-wrap gap-1.5">
            {alert.affectedAreas.map((area) => (
              <span key={area} className="text-[11px] bg-gray-50 dark:bg-white/5 border border-gray-200 dark:border-white/10 text-gray-600 dark:text-slate-300 px-2.5 py-1 rounded-full">
                {area}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="px-5 py-3 bg-gray-50 dark:bg-white/[0.02] border-t border-gray-100 dark:border-white/5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 text-[11px] text-gray-400 dark:text-slate-500">
          <Clock size={11} />
          <span>Issued: {formatTime(alert.issued)}</span>
        </div>
        <span className={`text-[11px] font-medium ${alert.severity === 'extreme' ? 'text-red-500 dark:text-red-400' : 'text-gray-400 dark:text-slate-400'}`}>
          {timeUntilExpiry(alert.expires)}
        </span>
      </div>

      {alert.safetyTips?.length > 0 && (
        <div className="bg-gray-50 dark:bg-white/[0.03] border-t border-gray-100 dark:border-white/5">
          <button
            onClick={() => setTipsOpen((p) => !p)}
            className="w-full flex items-center justify-between px-5 py-3 text-xs font-semibold text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-150"
          >
            <span className="flex items-center gap-2">
              <ShieldCheck size={13} className="text-teal-500 dark:text-teal-400" />
              Safety Tips
            </span>
            <span className="text-gray-400 dark:text-slate-500 text-[11px]">{tipsOpen ? '▴' : '▾'}</span>
          </button>
          {tipsOpen && (
            <ul className="px-5 pb-3 space-y-2">
              {alert.safetyTips.map((tip, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-teal-500 dark:bg-teal-400 shrink-0" />
                  <span className="text-xs text-gray-600 dark:text-slate-300 leading-relaxed">{tip}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
