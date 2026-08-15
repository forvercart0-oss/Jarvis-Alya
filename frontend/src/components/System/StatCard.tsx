export function StatCard({ title, value, unit, icon, error, loading }: {
  title: string
  value: number | null
  unit?: string
  icon: React.ReactNode
  error?: string
  loading?: boolean
}) {
  const display = loading ? '...' : error ? 'ERR' : value ?? '--'
  let color = 'text-cyan-400'
  if (typeof value === 'number') {
    if (value > 90) color = 'text-red-400'
    else if (value > 70) color = 'text-yellow-400'
  }

  return (
    <div className="glass-panel p-3 flex items-center gap-3">
      <div className={`p-2 rounded-lg bg-slate-800/80 ${color}`}>{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">{title}</div>
        <div className={`font-mono text-lg font-bold ${color}`}>
          {display}
          {unit && !error && <span className="text-xs text-slate-500 ml-1">{unit}</span>}
        </div>
        {error && <div className="text-[10px] text-red-400 truncate">{error}</div>}
      </div>
      {typeof value === 'number' && !error && (
        <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(100, value)}%`,
              backgroundColor: value > 90 ? '#f87171' : value > 70 ? '#facc15' : '#00f0ff',
            }}
          />
        </div>
      )}
    </div>
  )
}
