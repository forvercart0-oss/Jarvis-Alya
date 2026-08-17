import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../services/api'
import type { AdaptivePreference, Suggestion, EnvironmentProfile, PersonalizationAnalytics } from '../../types'

type SubTab = 'preferences' | 'workflows' | 'suggestions' | 'privacy' | 'analytics'

interface PersonalizationPanelProps {
  settings: any
}

export default function PersonalizationPanel({ settings }: PersonalizationPanelProps) {
  const [subTab, setSubTab] = useState<SubTab>('preferences')
  const [preferences, setPreferences] = useState<AdaptivePreference[]>([])
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [analytics, setAnalytics] = useState<PersonalizationAnalytics | null>(null)
  const [environment, setEnvironment] = useState<EnvironmentProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [newKey, setNewKey] = useState('')
  const [newValue, setNewValue] = useState('')
  const [exportData, setExportData] = useState<any>(null)

  const profile = settings?.persona || 'jarvis'

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [prefs, suggs, env] = await Promise.all([
        api.getAdaptivePreferences(profile),
        api.getPersonalizationSuggestions(profile),
        api.getEnvironmentProfile(),
      ])
      setPreferences(prefs)
      setSuggestions(suggs.suggestions || [])
      setEnvironment(env)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [profile])

  const loadAnalytics = useCallback(async () => {
    try {
      const data = await api.getPersonalizationAnalytics(profile)
      setAnalytics(data)
    } catch {
      // ignore
    }
  }, [profile])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    if (subTab === 'analytics') loadAnalytics()
  }, [subTab, loadAnalytics])

  const handleAddPreference = async () => {
    if (!newKey || !newValue) return
    try {
      await api.setAdaptivePreference({ key: newKey, value: newValue, source: 'explicit_user', confidence: 'high', profile })
      setNewKey('')
      setNewValue('')
      loadData()
    } catch {
      // ignore
    }
  }

  const handleForget = async (preference_id?: string, key?: string) => {
    try {
      await api.forgetPreference({ preference_id, key, profile })
      loadData()
    } catch {
      // ignore
    }
  }

  const handleExport = async () => {
    try {
      const data = await api.exportPersonalization(profile)
      setExportData(data)
    } catch {
      // ignore
    }
  }

  const handleImport = async () => {
    if (!exportData) return
    try {
      await api.importPersonalization({ data: exportData, profile })
      loadData()
      setExportData(null)
    } catch {
      // ignore
    }
  }

  const confidenceColor = (c: string) => {
    if (c === 'high') return 'text-emerald-400'
    if (c === 'medium') return 'text-yellow-400'
    return 'text-slate-500'
  }

  const subTabs: { id: SubTab; label: string }[] = [
    { id: 'preferences', label: 'Preferences' },
    { id: 'workflows', label: 'Workflows' },
    { id: 'suggestions', label: 'Suggestions' },
    { id: 'privacy', label: 'Privacy' },
    { id: 'analytics', label: 'Intelligence' },
  ]

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-cyan-500/10">
        <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Personalization</span>
      </div>

      <div className="flex border-b border-cyan-500/10">
        {subTabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setSubTab(t.id)}
            className={`px-3 py-2 text-xs tracking-wider uppercase transition-all ${
              subTab === t.id ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-400/5' : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading && <div className="text-xs text-slate-500">Loading personalization data...</div>}

        {subTab === 'preferences' && (
          <div className="space-y-3">
            <div className="glass-panel p-3 space-y-2">
              <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Add Preference</div>
              <div className="flex gap-2">
                <input
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  placeholder="Key"
                  className="flex-1 bg-slate-900/50 border border-slate-700/50 rounded px-2 py-1 text-xs text-slate-300 outline-none focus:border-cyan-500/50"
                />
                <input
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  placeholder="Value"
                  className="flex-1 bg-slate-900/50 border border-slate-700/50 rounded px-2 py-1 text-xs text-slate-300 outline-none focus:border-cyan-500/50"
                />
                <button onClick={handleAddPreference} className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded text-xs text-cyan-300 hover:bg-cyan-500/20 transition-all">
                  Save
                </button>
              </div>
            </div>

            {preferences.length === 0 && <div className="text-xs text-slate-600">No preferences learned yet.</div>}

            {preferences.map((pref) => (
              <motion.div
                key={pref.preference_id}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel p-3 flex items-center justify-between"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-slate-300 font-mono">{pref.key}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{pref.source}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${confidenceColor(pref.confidence)}`}>{pref.confidence}</span>
                  </div>
                  <div className="text-xs text-cyan-400/80 font-mono truncate">{pref.value}</div>
                  <div className="text-[10px] text-slate-600 mt-1">
                    Used {pref.usage_count} times
                  </div>
                </div>
                <button
                  onClick={() => handleForget(pref.preference_id)}
                  className="ml-3 px-2 py-1 text-[10px] text-red-400 hover:text-red-300 border border-red-500/20 rounded hover:bg-red-500/10 transition-all"
                >
                  Forget
                </button>
              </motion.div>
            ))}
          </div>
        )}

        {subTab === 'suggestions' && (
          <div className="space-y-3">
            {suggestions.length === 0 && <div className="text-xs text-slate-600">No suggestions yet.</div>}
            {suggestions.map((s) => (
              <motion.div
                key={s.suggestion_id}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel p-3"
              >
                <div className="text-xs text-slate-300 font-medium mb-1">{s.title}</div>
                <div className="text-[11px] text-slate-500 mb-3">{s.description}</div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded text-xs text-cyan-300 hover:bg-cyan-500/20 transition-all">
                    Create Skill
                  </button>
                  <button className="px-3 py-1 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all">
                    Not Now
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {subTab === 'analytics' && (
          <div className="space-y-3">
            {analytics ? (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="glass-panel p-3">
                    <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-1">Tasks Completed</div>
                    <div className="text-xl text-cyan-400 font-mono">{analytics.tasks_completed}</div>
                  </div>
                  <div className="glass-panel p-3">
                    <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-1">Success Rate</div>
                    <div className="text-xl text-emerald-400 font-mono">{(analytics.success_rate * 100).toFixed(0)}%</div>
                  </div>
                </div>
                {Object.keys(analytics.providers || {}).length > 0 && (
                  <div className="glass-panel p-3">
                    <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-2">Provider Usage</div>
                    {Object.entries(analytics.providers).map(([name, count]) => (
                      <div key={name} className="flex justify-between text-xs py-1">
                        <span className="text-slate-400 capitalize">{name}</span>
                        <span className="text-slate-300 font-mono">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <div className="text-xs text-slate-600">No analytics data yet.</div>
            )}
          </div>
        )}

        {subTab === 'privacy' && (
          <div className="space-y-3">
            <div className="glass-panel p-3">
              <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-2">Memory</div>
              <div className="text-xs text-slate-400 mb-3">All personalization data is stored locally and never shared.</div>
              <div className="flex gap-2">
                <button onClick={handleExport} className="px-3 py-1 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-300 hover:bg-slate-700 transition-all">
                  Export
                </button>
                {exportData && (
                  <button onClick={handleImport} className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded text-xs text-cyan-300 hover:bg-cyan-500/20 transition-all">
                    Import
                  </button>
                )}
              </div>
            </div>
            {environment && (
              <div className="glass-panel p-3">
                <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-2">Environment</div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-slate-500">OS</span><span className="text-slate-300 font-mono">{environment.os}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Arch</span><span className="text-slate-300 font-mono">{environment.architecture}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Python</span><span className="text-slate-300 font-mono">{environment.python_version}</span></div>
                </div>
              </div>
            )}
          </div>
        )}

        {subTab === 'workflows' && (
          <div className="space-y-3">
            <div className="text-xs text-slate-600">Workflow patterns will appear here after repeated use.</div>
          </div>
        )}
      </div>
    </div>
  )
}
