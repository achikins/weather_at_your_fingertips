export default function ChartCard({ title, icon: Icon, iconColor, children }) {
  return (
    <div className="rounded-2xl border border-gray-100 dark:border-white/5 bg-white dark:bg-[#1a2035] p-4 hover:border-gray-200 dark:hover:border-white/10 transition-colors animate-fade-in shadow-sm dark:shadow-none">
      <div className="flex items-center gap-2 mb-4">
        <Icon size={15} className={iconColor} />
        <h3 className="text-sm font-medium text-gray-900 dark:text-white">{title}</h3>
      </div>
      <div className="h-52">{children}</div>
    </div>
  )
}
