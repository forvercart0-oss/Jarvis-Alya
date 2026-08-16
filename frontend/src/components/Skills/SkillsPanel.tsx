import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Plus, Trash2, Edit3, ToggleLeft, ToggleRight, Download, Upload, RefreshCw, Activity, AlertTriangle, CheckCircle2, XCircle, FileCode2, X } from 'lucide-react'
import { api } from '../../services/api'
import type { Skill, SkillActivity } from '../../types'

const PRIORITY_COLORS = {
  high: 'text-red-400 border-red-400/30',
  normal: 'text-cyan-400 border-cyan-400/30',
  low: 'text-slate-400 border-slate-400/30',
}

const PRIORITY_LABELS = {
  high: 'High',
  normal: 'Normal',
  low: 'Low',
}

function SkillCard({ skill, onToggle, onEdit, onDelete, onExport }: {
  skill: Skill
  onToggle: (id: string, enabled: boolean) => void
  onEdit: (skill: Skill) => void
  onDelete: (id: string) => void
  onExport: (id: string) => void
}) {
  const permCount = Object.values(skill.permissions).filter(Boolean).length
  const capCount = skill.capabilities?.length || 0

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="glass-panel p-4 space-y-3"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center border border-cyan-400/30 bg-cyan-500/10"
          >
            <FileCode2 className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-slate-200">{skill.name}</h3>
            <p className="text-[10px] text-slate-500">v{skill.version} · {skill.author}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onToggle(skill.id, !skill.enabled)}
            className={`p-1.5 rounded transition-colors ${skill.enabled ? 'text-emerald-400 hover:text-emerald-300' : 'text-slate-500 hover:text-slate-400'}`}
            title={skill.enabled ? 'Disable' : 'Enable'}
          >
            {skill.enabled ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
          </button>
          <button
            onClick={() => onEdit(skill)}
            className="p-1.5 rounded text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors"
            title="Edit"
          >
            <Edit3 className="w-4 h-4" />
          </button>
          <button
            onClick={() => onExport(skill.id)}
            className="p-1.5 rounded text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors"
            title="Export"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(skill.id)}
            className="p-1.5 rounded text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <p className="text-xs text-slate-400 line-clamp-2">{skill.description}</p>

      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-[10px] px-2 py-0.5 rounded border ${PRIORITY_COLORS[skill.priority || 'normal']}`}>
          {PRIORITY_LABELS[skill.priority || 'normal']}
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800/50 text-slate-400 border border-slate-700/30">
          {permCount} permissions
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800/50 text-slate-400 border border-slate-700/30">
          {capCount} capabilities
        </span>
        {skill.category && (
          <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-400/20">
            {skill.category}
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-1">
        {(skill.triggers || []).slice(0, 6).map((t) => (
          <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800/50 text-slate-500 border border-slate-700/30">
            {t}
          </span>
        ))}
        {(skill.triggers || []).length > 6 && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800/50 text-slate-500 border border-slate-700/30">
            +{(skill.triggers || []).length - 6}
          </span>
        )}
      </div>
    </motion.div>
  )
}

function SkillEditor({ skill, onSave, onCancel }: {
  skill: Partial<Skill> | null
  onSave: (data: Partial<Skill>) => void
  onCancel: () => void
}) {
  const [form, setForm] = useState<Partial<Skill>>(skill || {
    id: '',
    name: '',
    version: '1.0.0',
    description: '',
    author: 'User',
    enabled: true,
    priority: 'normal',
    triggers: [],
    capabilities: [],
    instructions: [],
    permissions: {},
    uses_memory: false,
    category: '',
  })
  const [jsonMode, setJsonMode] = useState(false)
  const [jsonText, setJsonText] = useState('')
  const [jsonError, setJsonError] = useState('')

  useEffect(() => {
    if (jsonMode && form) {
      setJsonText(JSON.stringify(form, null, 2))
    }
  }, [jsonMode])

  const handleJsonSave = () => {
    try {
      const parsed = JSON.parse(jsonText)
      setForm(parsed)
      setJsonError('')
      setJsonMode(false)
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : 'Invalid JSON')
    }
  }

  const update = (patch: Partial<Skill>) => setForm((f) => ({ ...f, ...patch }))

  if (!form) return null

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
    >
      <div className="relative w-full max-w-2xl glass-panel shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-cyan-500/10 bg-jarvis-panel/95 backdrop-blur-md">
          <h2 className="text-sm tracking-[0.2em] text-cyan-400/70 uppercase">
            {skill?.id ? 'Edit Skill' : 'Create Skill'}
          </h2>
          <button onClick={onCancel} className="text-slate-400 hover:text-slate-200 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {jsonMode ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">JSON Editor</span>
                <div className="flex gap-2">
                  <button onClick={handleJsonSave} className="px-3 py-1 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all">
                    Apply JSON
                  </button>
                  <button onClick={() => setJsonMode(false)} className="px-3 py-1 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all">
                    Cancel
                  </button>
                </div>
              </div>
              <textarea
                value={jsonText}
                onChange={(e) => { setJsonText(e.target.value); setJsonError('') }}
                className="w-full h-96 bg-slate-900/80 border border-cyan-500/20 rounded p-3 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400/60"
                spellCheck={false}
              />
              {jsonError && <p className="text-xs text-red-400">{jsonError}</p>}
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Skill ID</label>
                  <input
                    type="text"
                    value={form.id || ''}
                    onChange={(e) => update({ id: e.target.value })}
                    disabled={!!skill?.id}
                    className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60 disabled:opacity-50"
                    placeholder="linux-helper"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Name</label>
                  <input
                    type="text"
                    value={form.name || ''}
                    onChange={(e) => update({ name: e.target.value })}
                    className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                    placeholder="Linux Helper"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Version</label>
                  <input
                    type="text"
                    value={form.version || ''}
                    onChange={(e) => update({ version: e.target.value })}
                    className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                    placeholder="1.0.0"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Category</label>
                  <input
                    type="text"
                    value={form.category || ''}
                    onChange={(e) => update({ category: e.target.value })}
                    className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                    placeholder="system"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Description</label>
                <textarea
                  value={form.description || ''}
                  onChange={(e) => update({ description: e.target.value })}
                  rows={2}
                  className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                  placeholder="What does this skill do?"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Triggers (comma-separated)</label>
                <input
                  type="text"
                  value={(form.triggers || []).join(', ')}
                  onChange={(e) => update({ triggers: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) })}
                  className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                  placeholder="linux, terminal, bash"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Instructions (one per line)</label>
                <textarea
                  value={(form.instructions || []).join('\n')}
                  onChange={(e) => update({ instructions: e.target.value.split('\n').filter(Boolean) })}
                  rows={3}
                  className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                  placeholder="Explain commands before executing them.&#10;Never run destructive commands without confirmation."
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Capabilities (comma-separated)</label>
                <input
                  type="text"
                  value={(form.capabilities || []).join(', ')}
                  onChange={(e) => update({ capabilities: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) })}
                  className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                  placeholder="terminal.read, terminal.execute"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Priority</label>
                  <select
                    value={form.priority || 'normal'}
                    onChange={(e) => update({ priority: e.target.value as Skill['priority'] })}
                    className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                  >
                    <option value="high">High</option>
                    <option value="normal">Normal</option>
                    <option value="low">Low</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Author</label>
                  <input
                    type="text"
                    value={form.author || ''}
                    onChange={(e) => update({ author: e.target.value })}
                    className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                  />
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.enabled || false}
                    onChange={(e) => update({ enabled: e.target.checked })}
                    className="rounded border-cyan-500/30 bg-slate-900/80 text-cyan-400 focus:ring-cyan-400"
                  />
                  <span className="text-xs text-slate-300">Enabled</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.uses_memory || false}
                    onChange={(e) => update({ uses_memory: e.target.checked })}
                    className="rounded border-cyan-500/30 bg-slate-900/80 text-cyan-400 focus:ring-cyan-400"
                  />
                  <span className="text-xs text-slate-300">Uses Memory</span>
                </label>
              </div>

              <div className="border-t border-cyan-500/10 pt-4">
                <h3 className="text-xs text-slate-400 mb-2">Permissions</h3>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries({
                    network: 'Network',
                    filesystem_read: 'Read Files',
                    filesystem_write: 'Write Files',
                    terminal: 'Terminal',
                    camera: 'Camera',
                    microphone: 'Microphone',
                    notifications: 'Notifications',
                    clipboard_read: 'Read Clipboard',
                    clipboard_write: 'Write Clipboard',
                    calls: 'Calls',
                    messages: 'Messages',
                    browser_read: 'Read Browser',
                    browser_control: 'Control Browser',
                  }).map(([key, label]) => (
                    <label key={key} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={!!form.permissions?.[key as keyof Skill['permissions']]}
                        onChange={(e) => update({
                          permissions: {
                            ...form.permissions,
                            [key]: e.target.checked,
                          } as Skill['permissions'],
                        })}
                        className="rounded border-cyan-500/30 bg-slate-900/80 text-cyan-400 focus:ring-cyan-400"
                      />
                      <span className="text-xs text-slate-300">{label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-cyan-500/10">
            <button
              onClick={() => setJsonMode(!jsonMode)}
              className="px-3 py-1.5 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all flex items-center gap-1"
            >
              <FileCode2 className="w-3 h-3" />
              {jsonMode ? 'Visual Editor' : 'JSON Editor'}
            </button>
            <div className="flex gap-2">
              <button onClick={onCancel} className="px-4 py-2 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all">
                Cancel
              </button>
              <button
                onClick={() => onSave(form)}
                className="px-4 py-2 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all"
              >
                Save Skill
              </button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function ActivityLog({ activities, onClose }: {
  activities: SkillActivity[]
  onClose: () => void
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
    >
      <div className="relative w-full max-w-xl glass-panel shadow-2xl max-h-[80vh] overflow-y-auto">
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-cyan-500/10 bg-jarvis-panel/95 backdrop-blur-md">
          <h2 className="text-sm tracking-[0.2em] text-cyan-400/70 uppercase">Skill Activity</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 space-y-2">
          {activities.length === 0 && (
            <p className="text-xs text-slate-500 text-center py-8">No activity recorded yet.</p>
          )}
          {activities.map((a) => (
            <div key={a.id} className="flex items-center justify-between p-3 rounded bg-slate-900/50 border border-slate-700/30">
              <div className="flex items-center gap-3">
                {a.result === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : a.result === 'denied' ? (
                  <XCircle className="w-4 h-4 text-red-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-yellow-400" />
                )}
                <div>
                  <p className="text-xs text-slate-300">{a.skill_name}</p>
                  <p className="text-[10px] text-slate-500">{a.action} · {a.permission}</p>
                </div>
              </div>
              <span className="text-[10px] text-slate-500">{new Date(a.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export function SkillsPanel() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'enabled' | 'disabled' | 'builtin' | 'custom'>('all')
  const [editorOpen, setEditorOpen] = useState(false)
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null)
  const [activityOpen, setActivityOpen] = useState(false)
  const [activities, setActivities] = useState<SkillActivity[]>([])
  const [error, setError] = useState<string | null>(null)

  const loadSkills = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.listSkills()
      setSkills(data)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load skills')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSkills()
  }, [loadSkills])

  const handleSave = async (data: Partial<Skill>) => {
    try {
      if (editingSkill?.id) {
        await api.updateSkill(editingSkill.id, data)
      } else {
        await api.createSkill(data)
      }
      setEditorOpen(false)
      setEditingSkill(null)
      loadSkills()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save skill')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this skill? This cannot be undone.')) return
    try {
      await api.deleteSkill(id)
      loadSkills()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete skill')
    }
  }

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      await api.toggleSkill(id, enabled)
      loadSkills()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to toggle skill')
    }
  }

  const handleExport = async (id: string) => {
    try {
      const json = await api.exportSkill(id)
      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${id}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to export skill')
    }
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const text = await file.text()
      const result = await api.importSkill(text)
      setSkills((prev) => [...prev, { ...result, id: result.id }] as Skill[])
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to import skill')
    }
    e.target.value = ''
  }

  const handleActivity = async (skillId?: string) => {
    try {
      const data = await api.getSkillActivity(skillId)
      setActivities(data)
      setActivityOpen(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load activity')
    }
  }

  const filtered = skills.filter((s) => {
    const q = search.toLowerCase()
    if (q && !s.name.toLowerCase().includes(q) && !s.description.toLowerCase().includes(q) && !(s.triggers || []).some((t) => t.includes(q))) {
      return false
    }
    if (filter === 'enabled') return s.enabled
    if (filter === 'disabled') return !s.enabled
    if (filter === 'builtin') return s.author === 'System'
    if (filter === 'custom') return s.author !== 'System'
    return true
  })

  const enabledCount = skills.filter((s) => s.enabled).length

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-medium text-slate-200">Skills</h2>
          <p className="text-xs text-slate-500">{enabledCount}/{skills.length} enabled</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadSkills}
            className="p-2 rounded text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors"
            title="Reload"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleActivity()}
            className="p-2 rounded text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors"
            title="Activity Log"
          >
            <Activity className="w-4 h-4" />
          </button>
          <label className="cursor-pointer p-2 rounded text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors" title="Import Skill">
            <Upload className="w-4 h-4" />
            <input type="file" accept=".json" onChange={handleImport} className="hidden" />
          </label>
          <button
            onClick={() => { setEditingSkill(null); setEditorOpen(true) }}
            className="p-2 rounded text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors"
            title="Create Skill"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search skills..."
            className="w-full bg-slate-900/50 border border-cyan-500/20 rounded pl-9 pr-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
          />
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as typeof filter)}
          className="bg-slate-900/50 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-cyan-400/60"
        >
          <option value="all">All</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
          <option value="builtin">Built-in</option>
          <option value="custom">Custom</option>
        </select>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded bg-red-500/10 border border-red-400/30 text-xs text-red-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-300">
            <X className="w-3 h-3" />
          </button>
        </div>
      )}

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-3 chat-scroll">
          <AnimatePresence>
            {filtered.map((skill) => (
              <SkillCard
                key={skill.id}
                skill={skill}
                onToggle={handleToggle}
                onEdit={(s) => { setEditingSkill(s); setEditorOpen(true) }}
                onDelete={handleDelete}
                onExport={handleExport}
              />
            ))}
          </AnimatePresence>
          {filtered.length === 0 && (
            <div className="text-center py-12 text-slate-500 text-xs">
              {search ? 'No skills match your search.' : 'No skills yet. Create one to get started.'}
            </div>
          )}
        </div>
      )}

      <AnimatePresence>
        {editorOpen && (
          <SkillEditor
            skill={editingSkill}
            onSave={handleSave}
            onCancel={() => { setEditorOpen(false); setEditingSkill(null) }}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {activityOpen && (
          <ActivityLog
            activities={activities}
            onClose={() => setActivityOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
