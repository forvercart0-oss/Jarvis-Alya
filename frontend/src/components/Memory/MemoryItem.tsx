import { useState } from 'react'
import type { MemoryItem } from '../../types'
import { Trash2, Tag, Edit3, Check, Clock, Shield } from 'lucide-react'

interface MemoryItemProps {
  memory: MemoryItem
  onDelete: (id: string) => void
  onUpdate?: (id: string, content: string, confidence?: number, source?: string) => void
}

export function MemoryItemComponent({ memory, onDelete, onUpdate }: MemoryItemProps) {
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(memory.value)
  const time = new Date(memory.timestamp)
  const timeStr = time.toLocaleString()

  const handleSave = () => {
    if (!editValue.trim() || editValue === memory.value) {
      setEditing(false)
      return
    }
    onUpdate?.(memory.id, editValue.trim(), memory.confidence, memory.source)
    setEditing(false)
  }

  return (
    <div className="glass-panel p-3 flex justify-between items-start gap-2 group">
      <div className="flex-1 min-w-0">
        {memory.category && (
          <div className="flex items-center gap-1 text-[10px] text-cyan-400/70 mb-1">
            <Tag className="w-3 h-3" />
            {memory.category}
            {memory.project && <span className="text-slate-500">• {memory.project}</span>}
            {memory.profile && <span className="text-slate-500">• {memory.profile}</span>}
          </div>
        )}
        {editing ? (
          <input
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1 text-xs text-slate-100 focus:outline-none focus:border-cyan-400/60"
            autoFocus
          />
        ) : (
          <div className="text-xs text-slate-300 break-words">{memory.value}</div>
        )}
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[10px] text-slate-600 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeStr}
          </span>
          {memory.confidence !== undefined && (
            <span className="text-[10px] text-slate-600">
              {Math.round((memory.confidence || 0) * 100)}%
            </span>
          )}
          {memory.source && (
            <span className="text-[10px] text-slate-600 flex items-center gap-1">
              <Shield className="w-3 h-3" />
              {memory.source}
            </span>
          )}
        </div>
      </div>
      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {onUpdate && (
          <button
            onClick={() => setEditing(!editing)}
            className="text-slate-400 hover:text-cyan-300 p-1"
            title="Edit memory"
          >
            {editing ? <Check className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
          </button>
        )}
        <button
          onClick={() => onDelete(memory.id)}
          className="text-red-400 hover:text-red-300 p-1"
          title="Delete memory"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
