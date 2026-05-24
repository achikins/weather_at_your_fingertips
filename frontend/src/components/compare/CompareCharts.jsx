import { useEffect, useState } from 'react'
import {
  ResponsiveContainer,
  AreaChart, Area,
  BarChart, Bar,
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import { Thermometer, CloudRain, Droplets, Wind } from 'lucide-react'
import { api } from '../../services/api'
import CustomTooltip from '../charts/CustomTooltip'
import ChartCard from '../charts/ChartCard'

const AXIS = { tick: { fill: '#64748b', fontSize: 10 }, axisLine: false, tickLine: false }

function computeSummary(data) {
  if (!data.length) return {}
  return {
    avgTemp: Math.round(data.reduce((s, m) => s + m.tempAvg, 0) / data.length),
    maxTemp: Math.round(Math.max(...data.map((m) => m.tempMax))),
    minTemp: Math.round(Math.min(...data.map((m) => m.tempMin))),
    totalRain: Math.round(data.reduce((s, m) => s + m.rainfall, 0)),
    avgHumidity: Math.round(data.reduce((s, m) => s + m.humidity, 0) / data.length),
    avgWind: Math.round(data.reduce((s, m) => s + m.windSpeed, 0) / data.length),
  }
}

const comparisonRows = [
  { label: 'Avg Temperature', key: 'avgTemp', unit: '°C', higher: 'warmer' },
  { label: 'Record High', key: 'maxTemp', unit: '°C', higher: 'hotter' },
  { label: 'Record Low', key: 'minTemp', unit: '°C', higher: 'warmer' },
  { label: 'Annual Rainfall', key: 'totalRain', unit: ' mm', higher: 'wetter' },
  { label: 'Avg Humidity', key: 'avgHumidity', unit: '%', higher: 'more humid' },
  { label: 'Avg Wind Speed', key: 'avgWind', unit: ' km/h', higher: 'windier' },
]

export default function CompareCharts({ city1, city2 }) {
  const [data1, setData1] = useState([])
  const [data2, setData2] = useState([])

  useEffect(() => {
    if (city1) api.getCityMonthly(city1.id).then((d) => setData1(d.monthly || [])).catch(() => setData1([]))
  }, [city1])

  useEffect(() => {
    if (city2) api.getCityMonthly(city2.id).then((d) => setData2(d.monthly || [])).catch(() => setData2([]))
  }, [city2])

  if (!city1 || !city2) return null

  const merged = data1.map((m, i) => ({
    month: m.month,
    city1_temp: m.tempAvg,
    city2_temp: data2[i]?.tempAvg,
    city1_rain: m.rainfall,
    city2_rain: data2[i]?.rainfall,
    city1_humidity: m.humidity,
    city2_humidity: data2[i]?.humidity,
    city1_wind: m.windSpeed,
    city2_wind: data2[i]?.windSpeed,
  }))

  const summary1 = computeSummary(data1)
  const summary2 = computeSummary(data2)

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="rounded-2xl border border-gray-100 dark:border-white/5 bg-white dark:bg-[#1a2035] overflow-hidden shadow-sm dark:shadow-none">
        <div className="px-5 py-3 border-b border-gray-100 dark:border-white/5">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">Annual Summary Comparison</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 dark:border-white/5">
                <th className="text-left px-5 py-3 text-xs text-gray-400 dark:text-slate-500 font-medium uppercase tracking-wider w-40">Metric</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-blue-500 dark:text-blue-400 uppercase tracking-wider">
                  <span className="flex items-center justify-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-500" />{city1.name}
                  </span>
                </th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-teal-500 dark:text-teal-400 uppercase tracking-wider">
                  <span className="flex items-center justify-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-teal-400" />{city2.name}
                  </span>
                </th>
                <th className="text-center px-4 py-3 text-xs text-gray-400 dark:text-slate-500 font-medium uppercase tracking-wider">Winner</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-white/5">
              {comparisonRows.map(({ label, key, unit, higher }) => {
                const v1 = summary1[key]
                const v2 = summary2[key]
                const diff = v1 - v2
                return (
                  <tr key={key} className="hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors">
                    <td className="px-5 py-3 text-gray-500 dark:text-slate-400 text-xs font-medium">{label}</td>
                    <td className={`px-4 py-3 text-center text-sm font-semibold ${diff > 0 ? 'text-blue-500 dark:text-blue-300' : 'text-gray-600 dark:text-slate-300'}`}>
                      {v1}{unit}
                    </td>
                    <td className={`px-4 py-3 text-center text-sm font-semibold ${diff < 0 ? 'text-teal-500 dark:text-teal-300' : 'text-gray-600 dark:text-slate-300'}`}>
                      {v2}{unit}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {diff === 0 ? (
                        <span className="text-[10px] text-gray-400 dark:text-slate-500">Tied</span>
                      ) : (
                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${diff > 0 ? 'bg-blue-50 dark:bg-blue-500/15 text-blue-600 dark:text-blue-300' : 'bg-teal-50 dark:bg-teal-500/15 text-teal-600 dark:text-teal-300'}`}>
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

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <ChartCard title="Average Temperature (°C)" icon={Thermometer} iconColor="text-orange-400">
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
              <XAxis dataKey="month" {...AXIS} />
              <YAxis {...AXIS} unit="°" />
              <Tooltip content={<CustomTooltip unit="°C" />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Area type="monotone" dataKey="city1_temp" name={city1.name} stroke="#3b82f6" fill="url(#c1Temp)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="city2_temp" name={city2.name} stroke="#14b8a6" fill="url(#c2Temp)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Monthly Rainfall (mm)" icon={CloudRain} iconColor="text-blue-400">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={merged} margin={{ top: 5, right: 5, left: -20, bottom: 0 }} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" {...AXIS} />
              <YAxis {...AXIS} unit="mm" />
              <Tooltip content={<CustomTooltip unit=" mm" />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Bar dataKey="city1_rain" name={city1.name} fill="#3b82f6" radius={[2, 2, 0, 0]} fillOpacity={0.8} />
              <Bar dataKey="city2_rain" name={city2.name} fill="#14b8a6" radius={[2, 2, 0, 0]} fillOpacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Relative Humidity (%)" icon={Droplets} iconColor="text-teal-400">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={merged} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" {...AXIS} />
              <YAxis {...AXIS} unit="%" domain={[0, 100]} />
              <Tooltip content={<CustomTooltip unit="%" />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Line type="monotone" dataKey="city1_humidity" name={city1.name} stroke="#3b82f6" strokeWidth={2} dot={{ r: 2 }} />
              <Line type="monotone" dataKey="city2_humidity" name={city2.name} stroke="#14b8a6" strokeWidth={2} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Wind Speed (km/h)" icon={Wind} iconColor="text-purple-400">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={merged} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" {...AXIS} />
              <YAxis {...AXIS} unit=" k" />
              <Tooltip content={<CustomTooltip unit=" km/h" />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Line type="monotone" dataKey="city1_wind" name={city1.name} stroke="#3b82f6" strokeWidth={2} dot={{ r: 2 }} />
              <Line type="monotone" dataKey="city2_wind" name={city2.name} stroke="#14b8a6" strokeWidth={2} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  )
}
