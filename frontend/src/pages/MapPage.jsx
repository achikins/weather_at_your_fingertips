import { useEffect, useState } from 'react'
import MapView from '../components/map/MapView'
import AlertCard from '../components/alerts/AlertCard'
import { api } from '../services/api'

export default function MapPage() {
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    api.getAllAlerts()
      .then((data) => setAlerts(data.alerts || []))
      .catch(() => setAlerts([]))
  }, [])

  const topAlerts = alerts
    .filter((a) => a.isActive !== false)
    .filter((a) => a.severity === 'extreme' || a.severity === 'high')
    .slice(0, 3)

  return (
    <div className="flex flex-col h-full gap-0">
      {/* Map takes most of the space */}
      <div className="flex-1 relative min-h-0">
        <MapView />
      </div>

      {/* Compact alert strip at bottom */}
      {topAlerts.length > 0 && (
        <div className="shrink-0 border-t border-gray-200 dark:border-white/5 bg-white/90 dark:bg-[#0f1629]/90 backdrop-blur-md px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-gray-500 dark:text-slate-500 font-medium uppercase tracking-wider shrink-0">Live Alerts</span>
            <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {topAlerts.map((alert) => (
                <AlertCard key={alert.id} alert={alert} compact />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
