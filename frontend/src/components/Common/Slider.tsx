interface SliderProps {
  label?: string
  value: number
  min?: number
  max?: number
  step?: number
  onChange: (value: number) => void
  display?: string
}

export function Slider({ label, value, min = 0, max = 100, step = 1, onChange, display }: SliderProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">{label}</span>
          <span className="text-[10px] text-cyan-400/80 font-mono">{display ?? value}</span>
        </div>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none bg-slate-700 cursor-pointer"
        style={{ accentColor: 'var(--accent)' }}
      />
    </div>
  )
}
