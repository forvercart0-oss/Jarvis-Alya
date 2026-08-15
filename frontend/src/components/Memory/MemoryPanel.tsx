import { useState } from 'react'
import type { MemoryItem } from '../../types'
import { Plus } from 'lucide-react'
import { MemoryItemComponent } from './MemoryItem'

interface MemoryPanelProps {
  memories: MemoryItem[]
  onAdd: (content: string, category?: string) => void
  onDelete: (key: string) => void
  onRefresh: () => void
}

export function MemoryPanel({ memories, onAdd, onDelete, onRefresh }: MemoryPanelProps) {
  const [newContent, setNewContent] = useState('')
  const [newCategory, setNewCategory] = useState('')
  const [showForm, setShowForm] = useState(false)

  const handleAdd = () => {
    if (!newContent.trim()) return
    onAdd(newContent.trim(), newCategory.trim() || undefined)
    setNewContent('')
    setNewCategory('')
    setShowForm(false)
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase">Memory Bank</h3>
        <div className="flex gap-2">
          <button
            onClick={onRefresh}
            className="text-[10px] tracking-widest text-slate-500 hover:text-cyan-300 transition-colors uppercase"
          >
            Refresh
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className="text-[10px] tracking-widest text-cyan-400 hover:text-cyan-300 transition-colors uppercase flex items-center gap-1"
          >
            <Plus className="w-3 h-3" /> Add
          </button>
        </div>
      </div>

      {showForm && (
        <div className="glass-panel p-3 space-y-2">
          <input
            type="text"
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            placeholder='Memory content...'
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
          />
          <input
            type="text"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
            placeholder='Category (optional)'
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
          />
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              disabled={!newContent.trim()}
              className="px-3 py-1 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all disabled:opacity-50"
            >
              Save
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {memories.length === 0 ? (
        <div className="text-center text-slate-500 py-10">No memories stored yet.</div>
      ) : (
        <div className="space-y-2">
          {memories.map((m) => (
            <MemoryItemComponent key={m.id} memory={m} onDelete={onDelete} />
          ))}
        </div>
      )}
    </div>
  )
}
