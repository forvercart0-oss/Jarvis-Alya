import type { Automation } from '../../types'
import { Plus } from 'lucide-react'
import { useState } from 'react'
import { AutomationCard } from './AutomationCard'

interface AutomationsPanelProps {
  automations: Automation[]
  onCreate: (automation: Omit<Automation, 'id'>) => void
  onUpdate: (id: string, patch: Partial<Automation>) => void
  onDelete: (id: string) => void
  onExecute: (id: string) => void
}

const TRIGGERS = [
  { value: 'time', label: 'Time (daily HH:MM)' },
  { value: 'keyword', label: 'Keyword (on message)' },
  { value: 'startup', label: 'Startup (once on boot)' },
]

const ACTIONS = [
  { value: 'speak', label: 'Speak (TTS)' },
  { value: 'command', label: 'Run command' },
  { value: 'notification', label: 'Notify (WebSocket)' },
]

const inputCls =
  'w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60'
const labelCls = 'text-[10px] tracking-widest text-slate-500 uppercase'

export function AutomationsPanel({ automations, onCreate, onUpdate, onDelete, onExecute }: AutomationsPanelProps) {
  const [showForm, setShowForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newTrigger, setNewTrigger] = useState('time')
  const [newAction, setNewAction] = useState('speak')
  const [newSchedule, setNewSchedule] = useState('')
  const [newKeywords, setNewKeywords] = useState('')
  const [newPayload, setNewPayload] = useState('')

  const handleCreate = () => {
    if (!newName.trim()) return
    const automation: Omit<Automation, 'id'> = {
      name: newName.trim(),
      trigger: newTrigger,
      action: newAction,
      schedule: newTrigger === 'time' ? newSchedule.trim() || undefined : undefined,
      keywords: newTrigger === 'keyword' ? newKeywords.split(',').map((k) => k.trim()).filter(Boolean) : undefined,
      action_payload: newPayload.trim() ? { text: newPayload.trim(), message: newPayload.trim(), command: newPayload.trim() } : undefined,
      enabled: true,
    }
    onCreate(automation)
    setNewName('')
    setNewSchedule('')
    setNewKeywords('')
    setNewPayload('')
    setShowForm(false)
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase">Automations</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="text-[10px] tracking-widest text-cyan-400 hover:text-cyan-300 transition-colors uppercase flex items-center gap-1"
        >
          <Plus className="w-3 h-3" /> New
        </button>
      </div>

      {showForm && (
        <div className="glass-panel p-3 space-y-2.5">
          <div className="space-y-1">
            <span className={labelCls}>Name</span>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder='e.g., Morning greeting'
              className={inputCls}
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <span className={labelCls}>Trigger</span>
              <select value={newTrigger} onChange={(e) => setNewTrigger(e.target.value)} className={inputCls}>
                {TRIGGERS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <span className={labelCls}>Action</span>
              <select value={newAction} onChange={(e) => setNewAction(e.target.value)} className={inputCls}>
                {ACTIONS.map((a) => (
                  <option key={a.value} value={a.value}>{a.label}</option>
                ))}
              </select>
            </div>
          </div>

          {newTrigger === 'time' && (
            <div className="space-y-1">
              <span className={labelCls}>Daily time (HH:MM)</span>
              <input
                type="text"
                value={newSchedule}
                onChange={(e) => setNewSchedule(e.target.value)}
                placeholder='e.g., 09:30'
                className={inputCls}
              />
            </div>
          )}

          {newTrigger === 'keyword' && (
            <div className="space-y-1">
              <span className={labelCls}>Keywords (comma separated)</span>
              <input
                type="text"
                value={newKeywords}
                onChange={(e) => setNewKeywords(e.target.value)}
                placeholder='e.g., good morning, greeting'
                className={inputCls}
              />
            </div>
          )}

          <div className="space-y-1">
            <span className={labelCls}>
              {newAction === 'speak' ? 'Text to speak' : newAction === 'command' ? 'Shell command' : 'Message'}
            </span>
            <input
              type="text"
              value={newPayload}
              onChange={(e) => setNewPayload(e.target.value)}
              placeholder={newAction === 'speak' ? 'Good morning, Sir.' : newAction === 'command' ? 'echo hello' : 'Automation triggered.'}
              className={inputCls}
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={!newName.trim()}
              className="px-3 py-1.5 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all disabled:opacity-50"
            >
              Create
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1.5 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {automations.length === 0 ? (
        <div className="text-center text-slate-500 py-10 text-xs">No automations configured.</div>
      ) : (
        <div className="space-y-2">
          {automations.map((a) => (
            <AutomationCard
              key={a.id}
              automation={a}
              onToggle={() => onUpdate(a.id, { enabled: !a.enabled })}
              onExecute={() => onExecute(a.id)}
              onDelete={() => onDelete(a.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
