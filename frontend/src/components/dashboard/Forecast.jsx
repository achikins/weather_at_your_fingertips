import { CloudRain, Droplets, Wind, Sun } from 'lucide-react'

const asDayLabel = (dateString) => {
  const date = new Date(`${dateString}T00:00:00`)
  return date.toLocaleDateString('en-AU', { weekday: 'short' })
}

const asDateLabel = (dateString) => {
  const date = new Date(`${dateString}T00:00:00`)
  return date.toLocaleDateString('en-AU', { day: 'numeric', month: 'short' })
}

const rounded = (value) => (typeof value === 'number' ? Math.round(value) : null)
const oneDecimal = (value) => (typeof value === 'number' ? value.toFixed(1) : null)

function ForecastCard({ row }) {
  const maxTemp = rounded(row.pred_max_temp_c)
  const minTemp = rounded(row.pred_min_temp_c)
  const avgTemp = rounded(row.pred_avg_temp_c)
  const rain = oneDecimal(row.pred_rain_mm)
  const humidity = oneDecimal(row.pred_avg_humidity_pct)
  const wind = oneDecimal(row.pred_wind_speed_kmh ?? row.pred_wind_speed_ms)
  const rainHeavy = (row.pred_rain_mm ?? 0) >= 5

  return (
    <div className="rounded-xl border border-gray-100 dark:border-white/10 bg-white dark:bg-[#1a2035] p-3 shadow-sm dark:shadow-none">
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-xs font-semibold text-gray-700 dark:text-slate-200">{asDayLabel(row.forecast_date)}</p>
          <p className="text-[11px] text-gray-400 dark:text-slate-500">{asDateLabel(row.forecast_date)}</p>
        </div>
        {rainHeavy ? (
          <CloudRain size={14} className="text-blue-400" />
        ) : (
          <Sun size={14} className="text-orange-400" />
        )}
      </div>

      <div className="flex items-center justify-between mb-2">
        <div className="text-left">
          <p className="text-xl font-bold text-gray-900 dark:text-white leading-none">{avgTemp ?? '--'}°</p>
        </div>
        <div className="space-y-0.5">
          <p className="text-[10px] text-gray-400 dark:text-slate-500">
            High <span className="text-gray-700 dark:text-slate-300 font-medium">{maxTemp ?? '--'}°</span>
          </p>
          <p className="text-[10px] text-gray-400 dark:text-slate-500">
            Low <span className="text-blue-500 dark:text-blue-400 font-medium">{minTemp ?? '--'}°</span>
          </p>
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px]">
          <span className="flex items-center gap-1 text-gray-400 dark:text-slate-500">
            <CloudRain size={11} className="text-blue-400" />
            Rainfall
          </span>
          <span className="text-gray-700 dark:text-slate-300">{rain ?? '--'} mm</span>
        </div>
        <div className="flex items-center justify-between text-[11px]">
          <span className="flex items-center gap-1 text-gray-400 dark:text-slate-500">
            <Droplets size={11} className="text-teal-400" />
            Humidity
          </span>
          <span className="text-gray-700 dark:text-slate-300">{humidity ?? '--'}%</span>
        </div>
        <div className="flex items-center justify-between text-[11px]">
          <span className="flex items-center gap-1 text-gray-400 dark:text-slate-500">
            <Wind size={11} className="text-purple-400" />
            Wind Speed
          </span>
          <span className="text-gray-700 dark:text-slate-300">{wind ?? '--'} km/h</span>
        </div>
      </div>
    </div>
  )
}

export default function Forecast({ forecast = [], currentDate = null, loading = false }) {
  const rows = Array.isArray(forecast) ? [...forecast] : []
  rows.sort((a, b) => (a.forecast_date || '').localeCompare(b.forecast_date || ''))

  const futureRows = currentDate
    ? rows.filter((row) => row?.forecast_date && row.forecast_date !== currentDate)
    : rows.filter((row) => row?.forecast_date)

  const nextSeven = futureRows.slice(0, 7)

  if (loading && !nextSeven.length) {
    return (
      <div className="flex flex-wrap justify-center gap-3 animate-pulse">
        {Array.from({ length: 7 }).map((_, idx) => (
          <div
            key={idx}
            className="w-full sm:w-[calc(50%-0.375rem)] md:w-[calc(33.333%-0.5rem)] xl:flex-1 xl:min-w-0"
          >
            <div className="h-32 rounded-xl bg-gray-100 dark:bg-white/5" />
          </div>
        ))}
      </div>
    )
  }

  if (!nextSeven.length) return null

  return (
    <div className="flex flex-wrap justify-center gap-3">
      {nextSeven.map((row) => (
        <div
          key={`${row.forecast_date}-${row.horizon_days}`}
          className="w-full sm:w-[calc(50%-0.375rem)] md:w-[calc(33.333%-0.5rem)] xl:flex-1 xl:min-w-0"
        >
          <ForecastCard row={row} />
        </div>
      ))}
    </div>
  )
}
