import { Thermometer, Droplets, Wind, CloudRain, Sun, Eye } from 'lucide-react'

const conditionEmoji = (condition) => {
  if (!condition) return '🌤'
  const c = condition.toLowerCase()
  if (c.includes('storm') || c.includes('cyclone')) return '⛈'
  if (c.includes('rain') || c.includes('shower')) return '🌧'
  if (c.includes('cloud')) return '⛅'
  if (c.includes('haze') || c.includes('humid')) return '🌫'
  if (c.includes('clear') || c.includes('sunny')) return '☀'
  return '🌤'
}

function StatCard({ icon: Icon, label, value, unit, color, bg, trend }) {
  return (
    <div className={`rounded-2xl border border-white/5 p-4 bg-[#1a2035] hover:border-white/10 transition-all duration-200 group`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`w-9 h-9 rounded-xl ${bg} flex items-center justify-center`}>
          <Icon size={16} className={color} />
        </div>
        {trend !== undefined && (
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${trend >= 0 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-white">
        {value}<span className="text-base font-normal text-slate-400 ml-0.5">{unit}</span>
      </p>
      <p className="text-xs text-slate-500 mt-1">{label}</p>
    </div>
  )
}

export default function WeatherCards({ current, monthly, city }) {
  if (!current || !monthly?.length) return null

  const avgTemp = Math.round(monthly.reduce((s, m) => s + m.tempAvg, 0) / monthly.length)
  const maxTemp = Math.max(...monthly.map((m) => m.tempMax))
  const minTemp = Math.min(...monthly.map((m) => m.tempMin))
  const totalRain = Math.round(monthly.reduce((s, m) => s + m.rainfall, 0))
  const avgHumidity = Math.round(monthly.reduce((s, m) => s + m.humidity, 0) / monthly.length)
  const avgWind = Math.round(monthly.reduce((s, m) => s + m.windSpeed, 0) / monthly.length)

  return (
    <div className="space-y-4">
      {/* Hero current condition card */}
      <div className="rounded-2xl border border-white/5 bg-gradient-to-br from-blue-600/10 via-[#1a2035] to-teal-600/5 p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-slate-400 text-sm mb-1">Current Conditions</p>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-bold text-white">{current.temp}°</span>
              <span className="text-xl text-slate-400">C</span>
            </div>
            <p className="text-slate-300 text-sm mt-1">{current.condition}</p>
            <p className="text-slate-500 text-xs mt-0.5">UV Index: {current.uvIndex}</p>
          </div>
          <div className="text-5xl leading-none">{conditionEmoji(current.condition)}</div>
        </div>
        {/* Quick stats row */}
        <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-white/5">
          {[
            { label: 'Humidity', value: `${current.humidity}%`, color: 'text-teal-400' },
            { label: 'Wind', value: `${current.windSpeed} km/h`, color: 'text-purple-400' },
            { label: 'Rainfall', value: `${current.rainfall} mm`, color: 'text-blue-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className="text-center">
              <p className={`text-sm font-semibold ${color}`}>{value}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Annual stat cards */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          icon={Thermometer}
          label="Annual Avg Temp"
          value={avgTemp}
          unit="°C"
          color="text-orange-400"
          bg="bg-orange-500/10"
        />
        <StatCard
          icon={CloudRain}
          label="Annual Rainfall"
          value={totalRain}
          unit=" mm"
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          icon={Droplets}
          label="Avg Humidity"
          value={avgHumidity}
          unit="%"
          color="text-teal-400"
          bg="bg-teal-500/10"
        />
        <StatCard
          icon={Wind}
          label="Avg Wind Speed"
          value={avgWind}
          unit=" km/h"
          color="text-purple-400"
          bg="bg-purple-500/10"
        />
      </div>

      {/* Temperature range card */}
      <div className="rounded-2xl border border-white/5 bg-[#1a2035] p-4">
        <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-3">Annual Temperature Range</p>
        <div className="flex items-center gap-3">
          <div className="text-center">
            <p className="text-xl font-bold text-blue-400">{minTemp}°</p>
            <p className="text-[10px] text-slate-500">Record Low</p>
          </div>
          <div className="flex-1 h-2 rounded-full bg-gradient-to-r from-blue-500 via-teal-400 to-orange-500 mx-2" />
          <div className="text-center">
            <p className="text-xl font-bold text-orange-400">{maxTemp}°</p>
            <p className="text-[10px] text-slate-500">Record High</p>
          </div>
        </div>
      </div>
    </div>
  )
}
