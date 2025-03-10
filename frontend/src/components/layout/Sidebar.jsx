import { NavLink } from 'react-router-dom'
import { Map, LayoutDashboard, GitCompare, Bell, CloudSun, ChevronRight } from 'lucide-react'
import { weatherAlerts } from '../../data/mockWeatherData'

const navItems = [
  { to: '/', icon: Map, label: 'Map', end: true },
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/compare', icon: GitCompare, label: 'Compare' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
]

const severityColors = {
  extreme: 'bg-red-500',
  high: 'bg-orange-500',
  moderate: 'bg-yellow-500',
  low: 'bg-blue-500',
}

export default function Sidebar() {
  const extremeAlerts = weatherAlerts.filter((a) => a.severity === 'extreme' || a.severity === 'high').length

  return (
    <aside className="w-16 lg:w-60 h-full bg-[#0f1629] border-r border-white/5 flex flex-col shrink-0 transition-all duration-300">
      {/* Logo */}
      <div className="px-3 lg:px-5 py-5 border-b border-white/5 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-teal-500 flex items-center justify-center shrink-0">
          <CloudSun size={18} className="text-white" />
        </div>
        <div className="hidden lg:block overflow-hidden">
          <p className="text-white font-semibold text-sm leading-tight">Weather at Your</p>
          <p className="text-teal-400 font-semibold text-sm leading-tight">Fingertips</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 lg:px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-2 lg:px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 relative
               ${
                 isActive
                   ? 'bg-blue-500/15 text-blue-400 border border-blue-500/20'
                   : 'text-slate-400 hover:bg-white/5 hover:text-slate-200 border border-transparent'
               }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={18}
                  className={`shrink-0 transition-colors ${isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300'}`}
                />
                <span className="hidden lg:block flex-1">{label}</span>
                {label === 'Alerts' && extremeAlerts > 0 && (
                  <span className="hidden lg:flex items-center justify-center w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-bold shrink-0">
                    {extremeAlerts}
                  </span>
                )}
                {label === 'Alerts' && extremeAlerts > 0 && (
                  <span className="lg:hidden absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-red-500 border-2 border-[#0f1629]" />
                )}
                {isActive && <ChevronRight size={14} className="hidden lg:block text-blue-400/60 shrink-0" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Alert Summary */}
      <div className="hidden lg:block px-3 py-4 border-t border-white/5">
        <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-3 px-1">Active Alerts</p>
        <div className="space-y-2">
          {weatherAlerts.slice(0, 3).map((alert) => (
            <div
              key={alert.id}
              className="flex items-center gap-2.5 px-2 py-2 rounded-lg bg-white/3 hover:bg-white/5 transition-colors cursor-pointer"
            >
              <span className={`w-2 h-2 rounded-full shrink-0 ${severityColors[alert.severity]} animate-pulse`} />
              <div className="min-w-0">
                <p className="text-xs text-slate-300 font-medium truncate">{alert.cityName}</p>
                <p className="text-[11px] text-slate-500 truncate">{alert.type}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-white/5">
        <p className="hidden lg:block text-[10px] text-slate-600 text-center">
          Data refreshed daily • BOM
        </p>
      </div>
    </aside>
  )
}
