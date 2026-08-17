import { useState, useEffect } from 'react'
import type { JarvisSettings } from '../../types'
import { api } from '../../services/api'
import { Zap, AlertTriangle } from 'lucide-react'

interface AutomationSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

type SubTab = 'modes' | 'scopes' | 'profiles' | 'dashboard'

const SCOPES = [
  { key: 'files', label: 'Files' },
  { key: 'terminal', label: 'Terminal' },
  { key: 'browser', label: 'Browser' },
  { key: 'applications', label: 'Applications' },
  { key: 'system', label: 'System' },
  { key: 'coding', label: 'Coding' },
  { key: 'documents', label: 'Documents' },
  { key: 'network', label: 'Network' },
  { key: 'communication', label: 'Communication' },
  { key: 'vision', label: 'Vision' },
  { key: 'automation', label: 'Automation' },
]

export function AutomationSettings({ settings, onUpdate }: AutomationSettingsProps) {
  const [subTab, setSubTab] = useState<SubTab>('modes')
  const [mode, setMode] = useState(settings.execution_mode || 'assisted')
  const [profile, setProfile] = useState(settings.automation_profile || 'safe')
  const [scopes, setScopes] = useState<Record<string, boolean>>({})
  const [dashboard, setDashboard] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setMode(settings.execution_mode || 'assisted')
    setProfile(settings.automation_profile || 'safe')
  }, [settings.execution_mode, settings.automation_profile])

  useEffect(() => {
    const loadScopes = async () => {
      try {
        const res = await api.getAutomationScopes()
        const scopeData = res.scopes || {}
        const map: Record<string, boolean> = {}
        for (const [key, val] of Object.entries(scopeData)) {
          map[key] = (val as any).enabled || false
        }
        setScopes(map)
      } catch {
        // ignore
      }
    }
    loadScopes()
  }, [])

  useEffect(() => {
    if (subTab === 'dashboard') {
      const loadDashboard = async () => {
        setLoading(true)
        try {
          const res = await api.getAutomationDashboard()
          setDashboard(res)
        } catch {
          // ignore
        } finally {
          setLoading(false)
        }
      }
      loadDashboard()
    }
  }, [subTab])

  const handleModeChange = async (newMode: string) => {
    setMode(newMode)
    onUpdate({ execution_mode: newMode })
    try {
      await api.setExecutionMode({ mode: newMode })
    } catch {
      // ignore
    }
  }

  const handleProfileChange = async (newProfile: string) => {
    setProfile(newProfile)
    onUpdate({ automation_profile: newProfile })
    try {
      await api.setAutomationProfile({ profile: newProfile })
    } catch {
      // ignore
    }
  }

  const handleScopeToggle = async (scope: string, enabled: boolean) => {
    const next = { ...scopes, [scope]: enabled }
    setScopes(next)
    const scopeKey = `automation_scope_${scope}` as any
    onUpdate({ [scopeKey]: enabled })
    try {
      await api.setAutomationScope({ scope, enabled })
    } catch {
      // ignore
    }
  }

  const handleEmergencyStop = async () => {
    try {
      await api.emergencyStop({})
    } catch {
      // ignore
    }
  }

  const subTabs: { id: SubTab; label: string }[] = [
    { id: 'modes', label: 'Modes' },
    { id: 'scopes', label: 'Scopes' },
    { id: 'profiles', label: 'Profiles' },
    { id: 'dashboard', label: 'Dashboard' },
  ]

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-500/10">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400/70" />
          <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">Automation</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${mode === 'full_auto' ? 'bg-emerald-500/20 text-emerald-400' : mode === 'safe' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-500/20 text-slate-400'}`}>
            {mode.toUpperCase()}
          </span>
        </div>
        <button onClick={handleEmergencyStop} className="flex items-center gap-1 px-2 py-1 bg-red-500/10 border border-red-500/30 rounded text-[10px] text-red-400 hover:bg-red-500/20 transition-all">
          <AlertTriangle className="w-3 h-3" />
          STOP ALL
        </button>
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

      <div className="flex-1 overflow-y-auto p-4 space-y-4 settings-scroll">
        {subTab === 'modes' && (
          <div className="space-y-3">
            <div className="glass-panel p-3">
              <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-2">Execution Mode</div>
              <div className="flex gap-2">
                {(['assisted', 'full_auto', 'safe'] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => handleModeChange(m)}
                    className={`flex-1 px-3 py-2 rounded border text-xs transition-all ${
                      mode === m
                        ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300'
                        : 'border-slate-700/30 bg-slate-900/50 text-slate-400 hover:text-slate-300'
                    }`}
                  >
                    {m === 'full_auto' ? '⚡ Full Auto' : m === 'safe' ? '🛡 Safe' : '🤝 Assisted'}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-slate-500 mt-2">
                {mode === 'full_auto' && 'JARVIS executes pre-authorized actions automatically without confirmation dialogs.'}
                {mode === 'safe' && 'JARVIS asks for confirmation before every action.'}
                {mode === 'assisted' && 'JARVIS asks for confirmation only for risky actions.'}
              </p>
            </div>
          </div>
        )}

        {subTab === 'scopes' && (
          <div className="space-y-2">
            <div className="glass-panel p-3">
              <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-2">Authorization Scopes</div>
              <p className="text-[10px] text-slate-500 mb-3">Enable categories to allow automatic execution without repeated confirmations.</p>
              <div className="space-y-2">
                {SCOPES.map((s) => (
                  <div key={s.key} className="flex items-center justify-between py-1.5">
                    <span className="text-xs text-slate-300">{s.label}</span>
                    <button
                      onClick={() => handleScopeToggle(s.key, !scopes[s.key])}
                      className={`w-10 h-5 rounded-full transition-all relative ${scopes[s.key] ? 'bg-emerald-500/30' : 'bg-slate-700/50'}`}
                    >
                      <div className={`w-3.5 h-3.5 rounded-full transition-all absolute top-0.5 ${scopes[s.key] ? 'translate-x-5 bg-emerald-400' : 'translate-x-0.5 bg-slate-400'}`} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {subTab === 'profiles' && (
          <div className="space-y-2">
            {['safe', 'development', 'full_auto'].map((p) => (
              <button
                key={p}
                onClick={() => handleProfileChange(p)}
                className={`w-full glass-panel p-3 text-left transition-all ${
                  profile === p ? 'border-cyan-500/40 bg-cyan-500/5' : 'hover:border-cyan-500/20'
                }`}
              >
                <div className="text-xs text-slate-200 font-medium capitalize">{p}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  {p === 'safe' && 'Minimal automation with confirmations'}
                  {p === 'development' && 'Development workflow automation'}
                  {p === 'full_auto' && 'All authorized categories enabled'}
                </div>
              </button>
            ))}
          </div>
        )}

        {subTab === 'dashboard' && (
          <div className="space-y-3">
            {loading ? (
              <div className="text-xs text-slate-500">Loading dashboard...</div>
            ) : dashboard ? (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="glass-panel p-3">
                    <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-1">Active Tasks</div>
                    <div className="text-xl text-cyan-400 font-mono">{dashboard.active_tasks}</div>
                  </div>
                  <div className="glass-panel p-3">
                    <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-1">Completed</div>
                    <div className="text-xl text-emerald-400 font-mono">{dashboard.completed_tasks}</div>
                  </div>
                </div>
                <div className="glass-panel p-3">
                  <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-2">Execution Mode</div>
                  <div className="text-xs text-slate-300 capitalize">{dashboard.execution_mode}</div>
                  <div className="text-[10px] text-slate-500 mt-1">Profile: {dashboard.profile}</div>
                </div>
              </>
            ) : (
              <div className="text-xs text-slate-600">No dashboard data yet.</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
