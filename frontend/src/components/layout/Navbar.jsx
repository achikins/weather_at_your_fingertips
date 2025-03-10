import { useLocation } from 'react-router-dom'
import { Bell, Calendar } from 'lucide-react'
import { weatherAlerts } from '../../data/mockWeatherData'

const pageTitles = {
  '/': { title: 'Interactive Map', subtitle: 'Explore weather across Australia' },
  '/dashboard': { title: 'Dashboard', subtitle: 'Detailed weather trends' },
  '/compare': { title: 'Compare Cities', subtitle: 'Side-by-side weather comparison' },
  '/alerts': { title: 'Weather Alerts', subtitle: 'Active warnings & advisories' },
}

const severityDot = {
  extreme: 'bg-red-500',
  high: 'bg-orange-500',
  moderate: 'bg-yellow-500',
  low: 'bg-blue-500',
}

export default function Navbar() {
  const { pathname } = useLocation()
  const page = pageTitles[pathname] || pageTitles['/']
  const activeAlerts = weatherAlerts.filter((a) => a.severity === 'extreme' || a.severity === 'high')

  const now = new Date()
  const dateStr = now.toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })

  return (
    <header className="h-14 bg-[#0f1629]/80 backdrop-blur-md border-b border-white/5 flex items-center px-4 lg:px-6 gap-4 shrink-0 z-10">
      {/* Page title */}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-white font-semibold text-base truncate">{page.title}</h1>
          <span className="hidden sm:block text-slate-500 text-sm">—</span>
          <p className="hidden sm:block text-slate-400 text-sm truncate">{page.subtitle}</p>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Date */}
        <div className="hidden md:flex items-center gap-1.5 text-slate-400 text-xs bg-white/5 px-3 py-1.5 rounded-lg border border-white/5">
          <Calendar size={13} />
          <span>{dateStr}</span>
        </div>

        {/* Alert severity indicators */}
        {activeAlerts.length > 0 && (
          <div className="hidden sm:flex items-center gap-1.5 bg-red-500/10 border border-red-500/20 px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-red-400 text-xs font-medium">{activeAlerts.length} active</span>
          </div>
        )}

        {/* Bell icon */}
        <button className="relative w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 flex items-center justify-center transition-colors">
          <Bell size={15} className="text-slate-400" />
          {activeAlerts.length > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-red-500" />
          )}
        </button>
      </div>
    </header>
  )
}
