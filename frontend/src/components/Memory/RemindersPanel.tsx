import { useState } from 'react'
import type { ReminderItem } from '../../types'
import { Plus, Trash2, Pause, Play } from 'lucide-react'

interface RemindersPanelProps {
  reminders: ReminderItem[]
  onAdd: (title: string, description: string, dueAt: string, repeat: string) => void
  onUpdate: (id: string, updates: Record<string, any>) => void
  onDelete: (id: string) => void
}

export function RemindersPanel({ reminders, onAdd, onUpdate, onDelete }: RemindersPanelProps) {
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [dueAt, setDueAt] = useState('')
  const [repeat, setRepeat] = useState('once')

  const handleAdd = () => {
    if (!title.trim() || !dueAt) return
    onAdd(title.trim(), description.trim(), dueAt, repeat)
    setTitle('')
    setDescription('')
    setDueAt('')
    setRepeat('once')
    setShowForm(false)
  }

  const toggleReminder = (r: ReminderItem) => {
    onUpdate(r.id, { enabled: r.enabled ? 0 : 1 })
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs tracking-widest text-slate-400 uppercase">Reminders</h4>
        <button
          onClick={() => setShowForm(!showForm)}
          className="text-[10px] tracking-widest text-cyan-400 hover:text-cyan-300 transition-colors uppercase flex items-center gap-1"
        >
          <Plus className="w-3 h-3" /> Add
        </button>
      </div>

      {showForm && (
        <div className="glass-panel p-3 space-y-2">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder='Title'
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
          />
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder='Description (optional)'
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
          />
          <input
            type="datetime-local"
            value={dueAt}
            onChange={(e) => setDueAt(e.target.value)}
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-400/60"
          />
          <select
            value={repeat}
            onChange={(e) => setRepeat(e.target.value)}
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-400/60"
          >
            <option value="once">Once</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              disabled={!title.trim() || !dueAt}
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

      {reminders.length === 0 ? (
        <div className="text-center text-slate-500 py-6">No reminders.</div>
      ) : (
        <div className="space-y-2">
          {reminders.map((r) => (
            <div key={r.id} className="glass-panel p-3 flex justify-between items-start gap-2">
              <div className="flex-1 min-w-0">
                <div className="text-xs text-slate-300">{r.title}</div>
                {r.description && <div className="text-[10px] text-slate-500 mt-1">{r.description}</div>}
                <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-600">
                  <span>{new Date(r.due_at).toLocaleString()}</span>
                  <span>• {r.repeat}</span>
                </div>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => toggleReminder(r)}
                  className="text-slate-400 hover:text-cyan-300 p-1"
                  title={r.enabled ? 'Pause' : 'Resume'}
                >
                  {r.enabled ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                </button>
                <button
                  onClick={() => onDelete(r.id)}
                  className="text-red-400 hover:text-red-300 p-1"
                  title="Delete"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
