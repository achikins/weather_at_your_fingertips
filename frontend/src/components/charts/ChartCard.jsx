import { BarChart2 } from 'lucide-react'

function NoDataState() {
  return (
    <div className="h-full flex flex-col items-center justify-center gap-2.5 text-center">
      <div className="w-10 h-10 rounded-xl bg-gray-50 dark:bg-white/5 flex items-center justify-center">
        <BarChart2 size={18} className="text-gray-300 dark:text-slate-600" />
      </div>
      <div>
        <p className="text-sm font-medium text-gray-400 dark:text-slate-500">No data available</p>
        <p className="text-xs text-gray-300 dark:text-slate-600 mt-0.5">Try adjusting your date or location filters</p>
      </div>
    </div>
  )
}

export default function ChartCard({ title, icon: Icon, iconColor, children, data }) {
  const isEmpty = Array.isArray(data) && data.length === 0

  return (
    <div className="rounded-2xl border border-gray-100 dark:border-white/5 bg-white dark:bg-[#1a2035] p-4 hover:border-gray-200 dark:hover:border-white/10 transition-colors animate-fade-in shadow-sm dark:shadow-none">
      <div className="flex items-center gap-2 mb-4">
        <Icon size={15} className={iconColor} />
        <h3 className="text-sm font-medium text-gray-900 dark:text-white">{title}</h3>
      </div>
      <div className="h-52">
        {isEmpty ? <NoDataState /> : children}
      </div>
    </div>
  )
}
