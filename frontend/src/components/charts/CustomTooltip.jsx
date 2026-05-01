export default function CustomTooltip({ active, payload, label, unit }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white dark:bg-[#1a2035] border border-gray-200 dark:border-white/10 rounded-xl px-3 py-2.5 shadow-xl text-xs">
      <p className="text-gray-500 dark:text-slate-400 font-medium mb-1.5">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 mb-0.5">
          <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-gray-600 dark:text-slate-300 capitalize">{entry.name}:</span>
          <span className="font-semibold text-gray-900 dark:text-white">
            {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
            {unit}
          </span>
        </div>
      ))}
    </div>
  )
}
