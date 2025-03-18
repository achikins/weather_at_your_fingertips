import { AlertTriangle, CloudLightning, Droplets, Wind, Waves, Thermometer, Clock, MapPin } from 'lucide-react'

const typeIcons = {
  'Severe Storm': CloudLightning,
  'Heavy Rainfall': Droplets,
  'Heatwave': Thermometer,
  'Strong Winds': Wind,
  'Coastal Hazard': Waves,
  'Thunderstorm': CloudLightning,
}

const severityConfig = {
  extreme: {
    badge: 'bg-red-500/20 text-red-300 border-red-500/30',
    border: 'border-l-red-500',
    icon: 'text-red-400',
    iconBg: 'bg-red-500/10',
    label: 'EXTREME',
    dot: 'bg-red-500',
  },
  high: {
    badge: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    border: 'border-l-orange-500',
    icon: 'text-orange-400',
    iconBg: 'bg-orange-500/10',
    label: 'HIGH',
    dot: 'bg-orange-500',
  },
  moderate: {
    badge: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    border: 'border-l-yellow-400',
    icon: 'text-yellow-400',
    iconBg: 'bg-yellow-500/10',
    label: 'MODERATE',
    dot: 'bg-yellow-400',
  },
  low: {
    badge: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    border: 'border-l-blue-400',
    icon: 'text-blue-400',
    iconBg: 'bg-blue-500/10',
    label: 'LOW',
    dot: 'bg-blue-400',
  },
}

const formatTime = (isoString) => {
  const d = new Date(isoString)
  return d.toLocaleString('en-AU', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
  })
}

const timeUntilExpiry = (isoString) => {
  const diff = new Date(isoString) - new Date()
  if (diff < 0) return 'Expired'
  const hours = Math.floor(diff / 3600000)
  if (hours < 24) return `Expires in ${hours}h`
  return `Expires in ${Math.floor(hours / 24)}d ${hours % 24}h`
}

export default function AlertCard({ alert, compact = false }) {
  const config = severityConfig[alert.severity] || severityConfig.low
  const Icon = typeIcons[alert.type] || AlertTriangle

  if (compact) {
    return (
      <div className={`flex items-center gap-3 px-3 py-2.5 rounded-xl bg-[#1a2035] border border-white/5 border-l-2 ${config.border} hover:border-white/10 transition-all duration-200`}>
        <span className={`w-2 h-2 rounded-full shrink-0 ${config.dot} animate-pulse`} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold text-white truncate">{alert.title}</p>
            <span className={`hidden sm:inline-flex shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded border ${config.badge}`}>
              {config.label}
            </span>
          </div>
          <p className="text-[10px] text-slate-500">{alert.cityName} · {alert.type}</p>
        </div>
        <span className="text-[10px] text-slate-500 shrink-0">{timeUntilExpiry(alert.expires)}</span>
      </div>
    )
  }

  return (
    <div className={`rounded-2xl bg-[#1a2035] border border-white/5 border-l-4 ${config.border} overflow-hidden hover:border-white/10 transition-all duration-200 animate-fade-in`}>
      {/* Header */}
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-start gap-3">
          <div className={`w-10 h-10 rounded-xl ${config.iconBg} flex items-center justify-center shrink-0 mt-0.5`}>
            <Icon size={18} className={config.icon} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start gap-2 flex-wrap">
              <h3 className="text-white font-semibold text-sm leading-tight">{alert.title}</h3>
              <span className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full border ${config.badge}`}>
                {config.label}
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <MapPin size={11} className="text-slate-500" />
              <p className="text-xs text-slate-400">{alert.cityName} · {alert.type}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Description */}
      <div className="px-5 pb-3">
        <p className="text-sm text-slate-300 leading-relaxed">{alert.description}</p>
      </div>

      {/* Affected areas */}
      {alert.affectedAreas?.length > 0 && (
        <div className="px-5 pb-3">
          <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider mb-2">Affected Areas</p>
          <div className="flex flex-wrap gap-1.5">
            {alert.affectedAreas.map((area) => (
              <span key={area} className="text-[11px] bg-white/5 border border-white/10 text-slate-300 px-2.5 py-1 rounded-full">
                {area}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Footer timestamps */}
      <div className="px-5 py-3 bg-white/2 border-t border-white/5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <Clock size={11} />
          <span>Issued: {formatTime(alert.issued)}</span>
        </div>
        <span className={`text-[11px] font-medium ${alert.severity === 'extreme' ? 'text-red-400' : 'text-slate-400'}`}>
          {timeUntilExpiry(alert.expires)}
        </span>
      </div>
    </div>
  )
}
