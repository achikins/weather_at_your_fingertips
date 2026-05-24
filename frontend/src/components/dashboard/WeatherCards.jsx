import { Thermometer, Droplets, Wind, CloudRain, TrendingUp, TrendingDown } from 'lucide-react'

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

function StatCard({ icon: Icon, label, value, unit, color, bg }) {
  return (
    <div className="rounded-2xl border border-gray-100 dark:border-white/5 p-4 bg-white dark:bg-[#1a2035] hover:border-gray-200 dark:hover:border-white/10 transition-all duration-200 shadow-sm dark:shadow-none flex items-center gap-3">
      <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center shrink-0`}>
        <Icon size={17} className={color} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-gray-400 dark:text-slate-500 truncate">{label}</p>
        <p className="text-lg font-bold text-gray-900 dark:text-white leading-tight">
          {value}<span className="text-xs font-normal text-gray-400 dark:text-slate-400 ml-0.5">{unit}</span>
        </p>
      </div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-gray-100 dark:border-white/5 p-4 bg-white dark:bg-[#1a2035] shadow-sm animate-pulse flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-gray-100 dark:bg-white/5 shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-2.5 bg-gray-100 dark:bg-white/5 rounded w-2/3" />
        <div className="h-4 bg-gray-100 dark:bg-white/5 rounded w-1/2" />
      </div>
    </div>
  )
}

export default function WeatherCards({ monthly, current, loading }) {
  if (loading && !monthly?.length) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    )
  }

  if (!monthly?.length) return null

  const latest      = monthly[monthly.length - 1]
  const avgTemp     = Math.round(monthly.reduce((s, m) => s + m.tempAvg, 0) / monthly.length)
  const totalRain   = Math.round(monthly.reduce((s, m) => s + m.rainfall, 0))
  const avgHumidity = (monthly.reduce((s, m) => s + m.humidity, 0) / monthly.length).toFixed(1)
  const avgWind     = (monthly.reduce((s, m) => s + m.windSpeed, 0) / monthly.length).toFixed(1)
  const displayTempRaw = current?.temp ?? latest.tempAvg
  const displayTemp = typeof displayTempRaw === 'number' ? Math.round(displayTempRaw) : displayTempRaw
  const dailyLowRaw = current?.tempMin ?? latest.tempMin
  const dailyHighRaw = current?.tempMax ?? latest.tempMax
  const dailyLow = typeof dailyLowRaw === 'number' ? Math.round(dailyLowRaw) : dailyLowRaw
  const dailyHigh = typeof dailyHighRaw === 'number' ? Math.round(dailyHighRaw) : dailyHighRaw
  const displayHumidity = current?.humidity ?? latest.humidity
  const displayWind = current?.windSpeed ?? latest.windSpeed
  const displayRain = current?.rainfall ?? latest.rainfall
  const currentLabel = current?.obsDate ? `Current (${current.obsDate})` : `${latest.month} average`

  return (
    <div className="space-y-3">
      {/* Current conditions hero strip */}
      <div className="rounded-2xl border border-gray-100 dark:border-white/5 bg-gradient-to-r from-blue-50 dark:from-blue-600/10 to-teal-50 dark:to-teal-600/5 px-5 py-4 shadow-sm dark:shadow-none flex flex-wrap items-center gap-6">
        <div className="flex items-center gap-3">
          <span className="text-4xl leading-none">{conditionEmoji('')}</span>
          <div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{displayTemp}°<span className="text-base font-normal text-gray-400 ml-0.5">C</span></p>
            <p className="text-sm text-gray-500 dark:text-slate-400">{currentLabel}</p>
          </div>
        </div>
        <div className="h-10 w-px bg-gray-200 dark:bg-white/10 hidden sm:block" />
        <div className="flex gap-5 text-sm">
          <div>
            <p className="text-teal-500 dark:text-teal-400 font-semibold">{displayHumidity}%</p>
            <p className="text-xs text-gray-400 dark:text-slate-500">Humidity</p>
          </div>
          <div>
            <p className="text-purple-500 dark:text-purple-400 font-semibold">{displayWind} km/h</p>
            <p className="text-xs text-gray-400 dark:text-slate-500">Wind</p>
          </div>
          <div>
            <p className="text-blue-500 dark:text-blue-400 font-semibold">{displayRain} mm</p>
            <p className="text-xs text-gray-400 dark:text-slate-500">Rainfall</p>
          </div>
        </div>
        <div className="ml-auto hidden md:flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <TrendingDown size={14} className="text-blue-400" />
            <span className="text-blue-500 dark:text-blue-400 font-semibold">{dailyLow}°</span>
            <span className="text-xs text-gray-400 dark:text-slate-500">Daily Low</span>
          </div>
          <div className="h-1.5 w-16 rounded-full bg-gradient-to-r from-blue-500 via-teal-400 to-orange-500" />
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-gray-400 dark:text-slate-500">Daily High</span>
            <span className="text-orange-500 dark:text-orange-400 font-semibold">{dailyHigh}°</span>
            <TrendingUp size={14} className="text-orange-400" />
          </div>
        </div>
      </div>

      {/* Stat cards row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard icon={Thermometer} label="Avg Temperature"  value={avgTemp}     unit="°C"    color="text-orange-400" bg="bg-orange-500/10" />
        <StatCard icon={CloudRain}   label="Total Rainfall"   value={totalRain}   unit=" mm"   color="text-blue-400"   bg="bg-blue-500/10" />
        <StatCard icon={Droplets}    label="Avg Humidity"     value={avgHumidity} unit="%"     color="text-teal-400"   bg="bg-teal-500/10" />
        <StatCard icon={Wind}        label="Avg Wind Speed"   value={avgWind}     unit=" km/h" color="text-purple-400" bg="bg-purple-500/10" />
      </div>
    </div>
  )
}
