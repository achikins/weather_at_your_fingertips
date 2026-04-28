import { ResponsiveContainer } from 'recharts'

export default function ChartCard({ title, icon: Icon, iconColor, children }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-[#1a2035] p-4 hover:border-white/10 transition-colors animate-fade-in">
      <div className="flex items-center gap-2 mb-4">
        <Icon size={15} className={iconColor} />
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>
      <div className="h-52">{children}</div>
    </div>
  )
}
