import type { MemoryItem } from '../../types'

interface MemoryTimelineProps {
  memories: MemoryItem[]
}

function groupByDate(memories: MemoryItem[]) {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 86400000)
  const weekAgo = new Date(today.getTime() - 7 * 86400000)

  const groups: Record<string, MemoryItem[]> = { Today: [], Yesterday: [], ThisWeek: [], Older: [] }
  for (const m of memories) {
    const d = new Date(m.timestamp)
    if (d >= today) groups.Today.push(m)
    else if (d >= yesterday) groups.Yesterday.push(m)
    else if (d >= weekAgo) groups.ThisWeek.push(m)
    else groups.Older.push(m)
  }
  return groups
}

export function MemoryTimeline({ memories }: MemoryTimelineProps) {
  const groups = groupByDate(memories)

  return (
    <div className="space-y-4">
      {Object.entries(groups).map(([label, items]) =>
        items.length === 0 ? null : (
          <div key={label} className="space-y-2">
            <h4 className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">{label}</h4>
            <div className="space-y-2">
              {items.map((m) => (
                <div key={m.id} className="glass-panel p-2 space-y-1">
                  <div className="text-xs text-slate-300 break-words">{m.value}</div>
                  <div className="flex items-center gap-2 text-[10px] text-slate-600">
                    <span>{m.category}</span>
                    {m.project && <span>• {m.project}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      )}
    </div>
  )
}
