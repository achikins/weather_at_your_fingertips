import {
  ResponsiveContainer,
  AreaChart, Area,
  BarChart, Bar,
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import { Thermometer, CloudRain, Droplets, Wind } from 'lucide-react'
import { getWeatherForCity } from '../../data/mockWeatherData'

const CustomTooltip = ({ active, payload, label, unit }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#1a2035] border border-white/10 rounded-xl px-3 py-2.5 shadow-2xl text-xs">
      <p className="text-slate-400 font-medium mb-1.5">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-white mb-0.5">
          <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-slate-300">{entry.name}:</span>
          <span className="font-semibold">{entry.value}{unit}</span>
        </div>
      ))}
    </div>
  )
}

function ChartCard({ title, icon: Icon, color, children }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-[#1a2035] p-4 hover:border-white/10 transition-colors">
      <div className="flex items-center gap-2 mb-4">
        <Icon size={15} className={color} />
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>
      <div className="h-52">{children}</div>
    </div>
  )
}

export default function CompareCharts({ city1, city2 }) {
  if (!city1 || !city2) return null

  const data1 = getWeatherForCity(city1.id)?.monthly || []
  const data2 = getWeatherForCity(city2.id)?.monthly || []

  // Merge data for combined charts
  const merged = data1.map((m, i) => ({
    month: m.month,
    [`${city1.name}_temp`]: m.tempAvg,
    [`${city2.name}_temp`]: data2[i]?.tempAvg,
    [`${city1.name}_rain`]: m.rainfall,
    [`${city2.name}_rain`]: data2[i]?.rainfall,
    [`${city1.name}_humidity`]: m.humidity,
    [`${city2.name}_humidity`]: data2[i]?.humidity,
    [`${city1.name}_wind`]: m.windSpeed,
    [`${city2.name}_wind`]: data2[i]?.windSpeed,
  }))

  // Annual summaries for comparison table
  const summary1 = {
    avgTemp: Math.round(data1.reduce((s, m) => s + m.tempAvg, 0) / data1.length),
    maxTemp: Math.max(...data1.map((m) => m.tempMax)),
    minTemp: Math.min(...data1.map((m) => m.tempMin)),
    totalRain: Math.round(data1.reduce((s, m) => s + m.rainfall, 0)),
    avgHumidity: Math.round(data1.reduce((s, m) => s + m.humidity, 0) / data1.length),
    avgWind: Math.round(data1.reduce((s, m) => s + m.windSpeed, 0) / data1.length),
  }
  const summary2 = {
    avgTemp: Math.round(data2.reduce((s, m) => s + m.tempAvg, 0) / data2.length),
    maxTemp: Math.max(...data2.map((m) => m.tempMax)),
    minTemp: Math.min(...data2.map((m) => m.tempMin)),
    totalRain: Math.round(data2.reduce((s, m) => s + m.rainfall, 0)),
    avgHumidity: Math.round(data2.reduce((s, m) => s + m.humidity, 0) / data2.length),
    avgWind: Math.round(data2.reduce((s, m) => s + m.windSpeed, 0) / data2.length),
  }

  const comparisonRows = [
    { label: 'Avg Temperature', key: 'avgTemp', unit: '°C', higher: 'warmer' },
    { label: 'Record High', key: 'maxTemp', unit: '°C', higher: 'hotter' },
    { label: 'Record Low', key: 'minTemp', unit: '°C', higher: 'warmer' },
    { label: 'Annual Rainfall', key: 'totalRain', unit: ' mm', higher: 'wetter' },
    { label: 'Avg Humidity', key: 'avgHumidity', unit: '%', higher: 'more humid' },
    { label: 'Avg Wind Speed', key: 'avgWind', unit: ' km/h', higher: 'windier' },
  ]

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Summary comparison table */}
      <div className="rounded-2xl border border-white/5 bg-[#1a2035] overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5">
          <h3 className="text-sm font-medium text-white">Annual Summary Comparison</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left px-5 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider w-40">Metric</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-blue-400 uppercase tracking-wider">
                  <span className="flex items-center justify-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-500" />
                    {city1.name}
                  </span>
                </th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-teal-400 uppercase tracking-wider">
                  <span className="flex items-center justify-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-teal-400" />
                    {city2.name}
                  </span>
                </th>
                <th className="text-center px-4 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider">Winner</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {comparisonRows.map(({ label, key, unit, higher }) => {
                const v1 = summary1[key]
                const v2 = summary2[key]
                const diff = v1 - v2
                return (
                  <tr key={key} className="hover:bg-white/2 transition-colors">
                    <td className="px-5 py-3 text-slate-400 text-xs font-medium">{label}</td>
                    <td className={`px-4 py-3 text-center text-sm font-semibold ${diff > 0 ? 'text-blue-300' : 'text-slate-300'}`}>
                      {v1}{unit}
                    </td>
                    <td className={`px-4 py-3 text-center text-sm font-semibold ${diff < 0 ? 'text-teal-300' : 'text-slate-300'}`}>
                      {v2}{unit}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {diff === 0 ? (
                        <span className="text-[10px] text-slate-500">Tied</span>
                      ) : (
                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${diff > 0 ? 'bg-blue-500/15 text-blue-300' : 'bg-teal-500/15 text-teal-300'}`}>
                          {diff > 0 ? city1.name : city2.name} · {higher}
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Temperature */}
        <ChartCard title="Average Temperature (°C)" icon={Thermometer} color="text-orange-400">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={merged} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="c1Temp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="c2Temp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} unit="°" />
              <Tooltip content={<CustomTooltip unit="°C" />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Area type="monotone" dataKey={`${city1.name}_temp`} name={city1.name} stroke="#3b82f6" fill="url(#c1Temp)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey={`${city2.name}_temp`} name={city2.name} stroke="#14b8a6" fill="url(#c2Temp)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Rainfall */}
        <ChartCard title="Monthly Rainfall (mm)" icon={CloudRain} color="text-blue-400">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={merged} margin={{ top: 5, right: 5, left: -20, bottom: 0 }} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} unit="mm" />
              <Tooltip content={<CustomTooltip unit=" mm" />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Bar dataKey={`${city1.name}_rain`} name={city1.name} fill="#3b82f6" radius={[2, 2, 0, 0]} fillOpacity={0.8} />
              <Bar dataKey={`${city2.name}_rain`} name={city2.name} fill="#14b8a6" radius={[2, 2, 0, 0]} fillOpacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Humidity */}
        <ChartCard title="Relative Humidity (%)" icon={Droplets} color="text-teal-400">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={merged} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} unit="%" domain={[0, 100]} />
              <Tooltip content={<CustomTooltip unit="%" />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Line type="monotone" dataKey={`${city1.name}_humidity`} name={city1.name} stroke="#3b82f6" strokeWidth={2} dot={{ r: 2 }} />
              <Line type="monotone" dataKey={`${city2.name}_humidity`} name={city2.name} stroke="#14b8a6" strokeWidth={2} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Wind */}
        <ChartCard title="Wind Speed (km/h)" icon={Wind} color="text-purple-400">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={merged} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} unit=" k" />
              <Tooltip content={<CustomTooltip unit=" km/h" />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Line type="monotone" dataKey={`${city1.name}_wind`} name={city1.name} stroke="#3b82f6" strokeWidth={2} dot={{ r: 2 }} />
              <Line type="monotone" dataKey={`${city2.name}_wind`} name={city2.name} stroke="#14b8a6" strokeWidth={2} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  )
}
