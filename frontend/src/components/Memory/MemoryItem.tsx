import type { MemoryItem } from '../../types'
import { Trash2, Tag } from 'lucide-react'

interface MemoryItemProps {
  memory: MemoryItem
  onDelete: (key: string) => void
}

export function MemoryItemComponent({ memory, onDelete }: MemoryItemProps) {
  const time = new Date(memory.timestamp)
  const timeStr = time.toLocaleString()

  return (
    <div className="glass-panel p-3 flex justify-between items-start gap-2 group">
      <div className="flex-1 min-w-0">
        {memory.category && (
          <div className="flex items-center gap-1 text-[10px] text-cyan-400/70 mb-1">
            <Tag className="w-3 h-3" />
            {memory.category}
          </div>
        )}
        <div className="text-xs text-slate-300 break-words">{memory.value}</div>
        <div className="text-[10px] text-slate-600 mt-1">{timeStr}</div>
      </div>
      <button
        onClick={() => onDelete(memory.key)}
        className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300 p-1"
        title="Delete memory"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  )
}
