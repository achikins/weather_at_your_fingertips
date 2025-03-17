import { Thermometer, Droplets, Wind, CloudRain } from 'lucide-react'

const layers = [
  { id: 'temperature', label: 'Temperature', icon: Thermometer, color: 'text-orange-400', activeBg: 'bg-orange-500/15 border-orange-500/30 text-orange-300' },
  { id: 'rainfall',    label: 'Rainfall',    icon: CloudRain,   color: 'text-blue-400',   activeBg: 'bg-blue-500/15 border-blue-500/30 text-blue-300' },
  { id: 'humidity',    label: 'Humidity',    icon: Droplets,    color: 'text-teal-400',   activeBg: 'bg-teal-500/15 border-teal-500/30 text-teal-300' },
  { id: 'wind',        label: 'Wind Speed',  icon: Wind,        color: 'text-purple-400', activeBg: 'bg-purple-500/15 border-purple-500/30 text-purple-300' },
]

export default function LayerToggle({ activeLayer, onLayerChange }) {
  return (
    <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
      <div className="bg-[#0f1629]/90 backdrop-blur-md border border-white/10 rounded-xl p-2 space-y-1.5 shadow-2xl">
        <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider px-1 pb-0.5">Data Layer</p>
        {layers.map(({ id, label, icon: Icon, color, activeBg }) => {
          const isActive = activeLayer === id
          return (
            <button
              key={id}
              onClick={() => onLayerChange(id)}
              className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-lg border text-xs font-medium transition-all duration-200
                ${isActive ? activeBg : 'border-transparent text-slate-400 hover:bg-white/5 hover:text-slate-200'}`}
            >
              <Icon size={14} className={isActive ? '' : color} />
              <span>{label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
