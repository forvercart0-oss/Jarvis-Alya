import { useState, useEffect } from 'react'
import type { JarvisSettings, AdaptivePreference, Suggestion, EnvironmentProfile, PersonalizationAnalytics } from '../../types'
import { api } from '../../services/api'
import { Trash2, Plus, RefreshCw, Download, Upload, Lightbulb, Shield } from 'lucide-react'

interface PersonalizationSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

type SubTab = 'preferences' | 'workflows' | 'suggestions' | 'privacy' | 'environment' | 'analytics'

export function PersonalizationSettings({ settings, onUpdate }: PersonalizationSettingsProps) {
  const [subTab, setSubTab] = useState<SubTab>('preferences')
  const [preferences, setPreferences] = useState<AdaptivePreference[]>([])
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [environment, setEnvironment] = useState<EnvironmentProfile | null>(null)
  const [analytics, setAnalytics] = useState<PersonalizationAnalytics | null>(null)
  const [loading, setLoading] = useState(false)
  const [newKey, setNewKey] = useState('')
  const [newValue, setNewValue] = useState('')
  const [exportData, setExportData] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    try {
      const [prefs, suggs, env, stats] = await Promise.all([
        api.getAdaptivePreferences(settings.persona || 'jarvis'),
        api.getPersonalizationSuggestions(settings.persona || 'jarvis'),
        api.getEnvironmentProfile(),
        api.getPersonalizationAnalytics(settings.persona || 'jarvis'),
      ])
      setPreferences(prefs)
      setSuggestions(suggs.suggestions || [])
      setEnvironment(env)
      setAnalytics(stats)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [settings.persona])

  const toggleSetting = (key: string, value: boolean) => {
    onUpdate({ [key]: value } as Partial<JarvisSettings>)
  }

  const addPreference = async () => {
    if (!newKey.trim() || !newValue.trim()) return
    await api.setAdaptivePreference({ key: newKey.trim(), value: newValue.trim(), profile: settings.persona || 'jarvis', source: 'explicit_user', confidence: 'high' })
    setNewKey('')
    setNewValue('')
    load()
  }

  const deletePreference = async (id: string) => {
    await api.deleteAdaptivePreference(id)
    load()
  }

  const handleExport = async () => {
    const data = await api.exportPersonalization(settings.persona || 'jarvis')
    setExportData(JSON.stringify(data, null, 2))
  }

  const handleImport = async () => {
    if (!exportData) return
    try {
      const data = JSON.parse(exportData)
      await api.importPersonalization({ data, profile: settings.persona || 'jarvis' })
      load()
    } catch {
      // silent
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-500/10">
        <h2 className="text-sm tracking-[0.2em] text-cyan-400/70 uppercase">Personalization</h2>
        <button onClick={load} className="text-slate-500 hover:text-cyan-300 transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="flex-1 overflow-hidden flex">
        <div className="w-40 border-r border-cyan-500/10 py-2 px-1 space-y-0.5">
          {[
            { id: 'preferences', label: 'Preferences' },
            { id: 'workflows', label: 'Workflows' },
            { id: 'suggestions', label: 'Suggestions' },
            { id: 'analytics', label: 'Analytics' },
            { id: 'environment', label: 'Environment' },
            { id: 'privacy', label: 'Privacy' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSubTab(tab.id as SubTab)}
              className={`w-full text-left px-3 py-1.5 text-xs rounded transition-colors ${
                subTab === tab.id
                  ? 'text-cyan-400 bg-cyan-500/10'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {subTab === 'preferences' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs tracking-widest text-slate-400 uppercase">Learned Preferences</h3>
                <div className="flex gap-2">
                  <button onClick={handleExport} className="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
                    <Download className="w-3 h-3" /> Export
                  </button>
                  <button onClick={handleImport} className="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
                    <Upload className="w-3 h-3" /> Import
                  </button>
                </div>
              </div>

              <div className="flex gap-2">
                <input
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  placeholder="Key"
                  className="flex-1 bg-slate-900 border border-cyan-500/20 rounded px-2 py-1 text-xs text-slate-300 placeholder:text-slate-600"
                />
                <input
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  placeholder="Value"
                  className="flex-1 bg-slate-900 border border-cyan-500/20 rounded px-2 py-1 text-xs text-slate-300 placeholder:text-slate-600"
                />
                <button onClick={addPreference} className="text-cyan-400 hover:text-cyan-300">
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                {preferences.map((pref) => (
                  <div key={pref.preference_id} className="flex items-center justify-between bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-slate-300 truncate">{pref.key}</div>
                      <div className="text-[10px] text-slate-500 truncate">{pref.value}</div>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        pref.confidence === 'high' ? 'bg-emerald-500/10 text-emerald-400' :
                        pref.confidence === 'medium' ? 'bg-amber-500/10 text-amber-400' :
                        'bg-slate-500/10 text-slate-400'
                      }`}>{pref.confidence}</span>
                      <button onClick={() => deletePreference(pref.preference_id)} className="text-slate-500 hover:text-red-400">
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
                {preferences.length === 0 && (
                  <div className="text-xs text-slate-600 text-center py-4">No learned preferences yet</div>
                )}
              </div>

              {exportData && (
                <textarea
                  value={exportData}
                  onChange={(e) => setExportData(e.target.value)}
                  className="w-full h-32 bg-slate-900 border border-cyan-500/20 rounded px-2 py-1 text-[10px] text-slate-400 font-mono"
                />
              )}
            </div>
          )}

          {subTab === 'workflows' && (
            <div className="space-y-4">
              <h3 className="text-xs tracking-widest text-slate-400 uppercase">Workflow Patterns</h3>
              <div className="text-xs text-slate-600 text-center py-4">Workflow detection requires repeated actions to identify patterns</div>
            </div>
          )}

          {subTab === 'suggestions' && (
            <div className="space-y-4">
              <h3 className="text-xs tracking-widest text-slate-400 uppercase">Suggestions</h3>
              {suggestions.map((s) => (
                <div key={s.suggestion_id} className="bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-3">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-400 mt-0.5" />
                    <div>
                      <div className="text-xs text-slate-300">{s.title}</div>
                      <div className="text-[10px] text-slate-500 mt-1">{s.description}</div>
                    </div>
                  </div>
                </div>
              ))}
              {suggestions.length === 0 && (
                <div className="text-xs text-slate-600 text-center py-4">No suggestions yet</div>
              )}
            </div>
          )}

          {subTab === 'analytics' && (
            <div className="space-y-4">
              <h3 className="text-xs tracking-widest text-slate-400 uppercase">Performance Analytics</h3>
              {analytics && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                    <div className="text-[10px] text-slate-500 uppercase">Tasks Completed</div>
                    <div className="text-lg text-cyan-400">{analytics.tasks_completed}</div>
                  </div>
                  <div className="bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                    <div className="text-[10px] text-slate-500 uppercase">Success Rate</div>
                    <div className="text-lg text-emerald-400">{(analytics.success_rate * 100).toFixed(0)}%</div>
                  </div>
                  <div className="bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                    <div className="text-[10px] text-slate-500 uppercase">Tasks Failed</div>
                    <div className="text-lg text-red-400">{analytics.tasks_failed}</div>
                  </div>
                  <div className="bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                    <div className="text-[10px] text-slate-500 uppercase">Sample Size</div>
                    <div className="text-lg text-slate-300">{analytics.sample_size}</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {subTab === 'environment' && (
            <div className="space-y-4">
              <h3 className="text-xs tracking-widest text-slate-400 uppercase">Environment Profile</h3>
              {environment && (
                <div className="space-y-2">
                  {Object.entries(environment).filter(([k]) => !['metadata'].includes(k)).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                      <div className="text-[10px] text-slate-500 uppercase">{key.replace(/_/g, ' ')}</div>
                      <div className="text-xs text-slate-300">{Array.isArray(value) ? value.join(', ') || 'None' : String(value)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {subTab === 'privacy' && (
            <div className="space-y-4">
              <h3 className="text-xs tracking-widest text-slate-400 uppercase">Privacy & Data</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                  <div>
                    <div className="text-xs text-slate-300">Enable Personalization</div>
                    <div className="text-[10px] text-slate-500">Allow JARVIS to learn from interactions</div>
                  </div>
                  <button
                    onClick={() => toggleSetting('personalization_enabled', !settings.personalization_enabled)}
                    className={`w-8 h-4 rounded-full transition-colors ${settings.personalization_enabled ? 'bg-cyan-500' : 'bg-slate-700'}`}
                  >
                    <div className={`w-3 h-3 rounded-full bg-white transition-transform ${settings.personalization_enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                  </button>
                </div>
                <div className="flex items-center justify-between bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                  <div>
                    <div className="text-xs text-slate-300">Ask Before Remembering</div>
                    <div className="text-[10px] text-slate-500">Confirm before saving preferences</div>
                  </div>
                  <button
                    onClick={() => toggleSetting('personalization_ask_before_remember', !settings.personalization_ask_before_remember)}
                    className={`w-8 h-4 rounded-full transition-colors ${settings.personalization_ask_before_remember ? 'bg-cyan-500' : 'bg-slate-700'}`}
                  >
                    <div className={`w-3 h-3 rounded-full bg-white transition-transform ${settings.personalization_ask_before_remember ? 'translate-x-4' : 'translate-x-0.5'}`} />
                  </button>
                </div>
                <div className="flex items-center justify-between bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                  <div>
                    <div className="text-xs text-slate-300">Enable Analytics</div>
                    <div className="text-[10px] text-slate-500">Track local performance metrics</div>
                  </div>
                  <button
                    onClick={() => toggleSetting('personalization_analytics_enabled', !settings.personalization_analytics_enabled)}
                    className={`w-8 h-4 rounded-full transition-colors ${settings.personalization_analytics_enabled ? 'bg-cyan-500' : 'bg-slate-700'}`}
                  >
                    <div className={`w-3 h-3 rounded-full bg-white transition-transform ${settings.personalization_analytics_enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
                  </button>
                </div>
                <div className="flex items-center justify-between bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-2">
                  <div>
                    <div className="text-xs text-slate-300">Cross-Device Sync</div>
                    <div className="text-[10px] text-slate-500">Sync preferences across devices</div>
                  </div>
                  <button
                    onClick={() => toggleSetting('personalization_cross_device_sync', !settings.personalization_cross_device_sync)}
                    className={`w-8 h-4 rounded-full transition-colors ${settings.personalization_cross_device_sync ? 'bg-cyan-500' : 'bg-slate-700'}`}
                  >
                    <div className={`w-3 h-3 rounded-full bg-white transition-transform ${settings.personalization_cross_device_sync ? 'translate-x-4' : 'translate-x-0.5'}`} />
                  </button>
                </div>
                <div className="bg-slate-900/50 border border-cyan-500/10 rounded px-3 py-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="w-4 h-4 text-cyan-400" />
                    <div className="text-xs text-slate-300">Privacy Controls</div>
                  </div>
                  <div className="text-[10px] text-slate-500 leading-relaxed">
                    All personalization data is stored locally by default. Cross-device sync is opt-in and only syncs approved preferences. Passwords, API keys, and tokens are never stored or synced.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}