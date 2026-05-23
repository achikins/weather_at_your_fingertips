import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Bell, Calendar, Sun, Moon } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'
import { api } from '../../services/api'

const pageTitles = {
  '/':          { title: 'Interactive Map',    subtitle: 'Explore weather across Australia' },
  '/dashboard': { title: 'Dashboard',          subtitle: 'Detailed weather trends' },
  '/compare':   { title: 'Compare Cities',     subtitle: 'Side-by-side weather comparison' },
  '/alerts':    { title: 'Weather Alerts',     subtitle: 'Active warnings & advisories' },
}

export default function Navbar() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { theme, toggleTheme } = useTheme()
  const page = pageTitles[pathname] || pageTitles['/']
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    api.getAllAlerts()
      .then((data) => setAlerts(data.alerts || []))
      .catch(() => setAlerts([]))
  }, [])

  const activeAlerts = alerts.filter((a) => a.isActive !== false)

  const dateStr = new Date().toLocaleDateString('en-AU', {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
  })

  return (
    <header className="h-14 bg-white/80 dark:bg-[#0f1629]/80 backdrop-blur-md border-b border-gray-200 dark:border-white/5 flex items-center px-4 lg:px-6 gap-4 shrink-0 z-10">
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-gray-900 dark:text-white font-semibold text-base truncate">{page.title}</h1>
          <span className="hidden sm:block text-gray-400 dark:text-slate-500 text-sm">—</span>
          <p className="hidden sm:block text-gray-500 dark:text-slate-400 text-sm truncate">{page.subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {/* Date */}
        <div className="hidden md:flex items-center gap-1.5 text-gray-500 dark:text-slate-400 text-xs bg-gray-100 dark:bg-white/5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-white/5">
          <Calendar size={13} />
          <span>{dateStr}</span>
        </div>

        {/* Alert count */}
        {activeAlerts.length > 0 && (
          <div className="hidden sm:flex items-center gap-1.5 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-red-600 dark:text-red-400 text-xs font-medium">{activeAlerts.length} active</span>
          </div>
        )}

        {/* Bell — navigates to alerts */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative w-8 h-8 rounded-lg bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 border border-gray-200 dark:border-white/5 flex items-center justify-center transition-colors"
        >
          <Bell size={15} className="text-gray-500 dark:text-slate-400" />
          {activeAlerts.length > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-red-500" />
          )}
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-white/5 hover:bg-gray-200 dark:hover:bg-white/10 border border-gray-200 dark:border-white/5 flex items-center justify-center transition-colors"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark'
            ? <Sun size={15} className="text-yellow-400" />
            : <Moon size={15} className="text-gray-500" />
          }
        </button>
      </div>
    </header>
  )
}
