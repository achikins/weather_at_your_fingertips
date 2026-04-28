export default function CustomTooltip({ active, payload, label, unit }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#1a2035] border border-white/10 rounded-xl px-3 py-2.5 shadow-2xl text-xs">
      <p className="text-slate-400 font-medium mb-1.5">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-white mb-0.5">
          <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-slate-300 capitalize">{entry.name}:</span>
          <span className="font-semibold">
            {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
            {unit}
          </span>
        </div>
      ))}
    </div>
  )
}
