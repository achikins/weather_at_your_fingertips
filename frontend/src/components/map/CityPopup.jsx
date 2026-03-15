import { X, Thermometer, Droplets, Wind, CloudRain, Sun } from 'lucide-react'
import { getWeatherForCity } from '../../data/mockWeatherData'

const conditionIcon = (condition) => {
  if (!condition) return '🌤'
  const c = condition.toLowerCase()
  if (c.includes('storm') || c.includes('cyclone')) return '⛈'
  if (c.includes('rain') || c.includes('shower')) return '🌧'
  if (c.includes('cloud')) return '⛅'
  if (c.includes('haze') || c.includes('humid')) return '🌫'
  if (c.includes('clear') || c.includes('sunny')) return '☀'
  return '🌤'
}

const severityColors = {
  extreme: 'bg-red-500/20 text-red-300 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  moderate: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  low: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
}

export default function CityPopup({ city, alerts = [], onClose }) {
  if (!city) return null
  const weather = getWeatherForCity(city.id)
  const current = weather?.current
  const monthly = weather?.monthly || []

  // Annual averages
  const avgTemp = monthly.length ? Math.round(monthly.reduce((s, m) => s + m.tempAvg, 0) / monthly.length) : '--'
  const totalRainfall = monthly.length ? Math.round(monthly.reduce((s, m) => s + m.rainfall, 0)) : '--'
  const avgHumidity = monthly.length ? Math.round(monthly.reduce((s, m) => s + m.humidity, 0) / monthly.length) : '--'

  return (
    <div className="absolute bottom-6 left-4 z-10 w-72 animate-fade-in">
      <div className="bg-[#0f1629]/95 backdrop-blur-md border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="relative px-4 pt-4 pb-3 bg-gradient-to-r from-blue-600/20 to-teal-600/10">
          <button
            onClick={onClose}
            className="absolute top-3 right-3 w-6 h-6 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
          >
            <X size={12} className="text-white" />
          </button>
          <div className="flex items-start gap-3">
            <div className="text-3xl leading-none mt-0.5">{conditionIcon(current?.condition)}</div>
            <div>
              <h3 className="text-white font-semibold text-base leading-tight">{city.name}</h3>
              <p className="text-slate-400 text-xs">{city.state}</p>
              {current && (
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-2xl font-bold text-white">{current.temp}°</span>
                  <span className="text-sm text-slate-400">C</span>
                </div>
              )}
              {current && <p className="text-xs text-slate-400 mt-0.5">{current.condition}</p>}
            </div>
          </div>
        </div>

        {/* Current conditions grid */}
        {current && (
          <div className="grid grid-cols-3 gap-px bg-white/5 mx-4 my-3 rounded-xl overflow-hidden">
            {[
              { icon: Droplets, label: 'Humidity', value: `${current.humidity}%`, color: 'text-teal-400' },
              { icon: Wind, label: 'Wind', value: `${current.windSpeed} km/h`, color: 'text-purple-400' },
              { icon: CloudRain, label: 'Rain', value: `${current.rainfall} mm`, color: 'text-blue-400' },
            ].map(({ icon: Icon, label, value, color }) => (
              <div key={label} className="bg-[#1a2035] px-2 py-2 text-center">
                <Icon size={13} className={`${color} mx-auto mb-1`} />
                <p className="text-white text-xs font-medium">{value}</p>
                <p className="text-slate-500 text-[10px]">{label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Annual stats */}
        <div className="px-4 pb-3">
          <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider mb-2">Annual Averages</p>
          <div className="flex gap-4 text-xs">
            <div>
              <span className="text-slate-400">Temp </span>
              <span className="text-white font-medium">{avgTemp}°C</span>
            </div>
            <div>
              <span className="text-slate-400">Rain </span>
              <span className="text-white font-medium">{totalRainfall} mm/yr</span>
            </div>
            <div>
              <span className="text-slate-400">RH </span>
              <span className="text-white font-medium">{avgHumidity}%</span>
            </div>
          </div>
        </div>

        {/* Active alerts */}
        {alerts.length > 0 && (
          <div className="px-4 pb-4">
            <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider mb-2">Active Alerts</p>
            <div className="space-y-1.5">
              {alerts.slice(0, 2).map((alert) => (
                <div key={alert.id} className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs ${severityColors[alert.severity]}`}>
                  <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />
                  <span className="font-medium truncate">{alert.title}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* City description */}
        <div className="px-4 pb-4">
          <p className="text-[11px] text-slate-500 leading-relaxed">{city.description}</p>
        </div>
      </div>
    </div>
  )
}
