import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Cpu, MemoryStick, HardDrive, Radio, AudioLines, Zap, ArrowUpRight } from 'lucide-react'
import type { HealthStatus, JarvisSettings, OrbState, SystemStats, TabId, VoiceInfo, CodingProject, DiagnosticInfo } from '../../types'
import { Orb } from '../Orb/Orb'
import { QuickActions } from './QuickActions'

interface HomePanelProps {
  settings: JarvisSettings | null
  health: HealthStatus | null
  voiceInfo: VoiceInfo | null
  diagnostics: DiagnosticInfo | null
  stats: SystemStats | null
  projects: CodingProject[]
  connection: 'connecting' | 'online' | 'offline'
  orbState: OrbState
  accentColor: string
  onNavigate: (tab: TabId) => void
  onAction: (action: string) => void
}

function fmtUptime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function fmtTimestamp(iso: string | null) {
  if (!iso) return 'never'
  try {
    return new Date(iso).toLocaleDateString()
  } catch {
    return 'unknown'
  }
}

export function HomePanel({ settings, health, voiceInfo, diagnostics, stats, projects, connection, orbState, accentColor, onNavigate, onAction }: HomePanelProps) {
  const [greeting, setGreeting] = useState('Welcome back')
  const onlineProviders = health?.providers
    ? Object.values(health.providers).filter((p) => p.status === 'online')
    : []

  useEffect(() => {
    const h = new Date().getHours()
    if (h < 5) setGreeting('Working late, I see')
    else if (h < 12) setGreeting('Good morning')
    else if (h < 18) setGreeting('Good afternoon')
    else setGreeting('Good evening')
  }, [])

  const miniStats = [
    { label: 'CPU', value: stats?.cpu.percent ?? null, unit: '%', icon: Cpu },
    { label: 'RAM', value: stats?.ram.percent ?? null, unit: '%', icon: MemoryStick },
    { label: 'Disk', value: stats?.disk.percent ?? null, unit: '%', icon: HardDrive },
  ]

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">
              {greeting}, <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-400">{settings?.user_name || 'Sir'}</span>
            </h1>
            <p className="text-xs text-slate-500 mt-1">{settings?.assistant_name || 'JARVIS'} is at your service. How can I help today?</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md glass-panel">
              <span className={`w-1.5 h-1.5 rounded-full ${connection === 'online' ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]' : connection === 'connecting' ? 'bg-yellow-400 animate-pulse' : 'bg-red-400'}`} />
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">{connection}</span>
            </div>
            {onlineProviders.length > 0 && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md glass-panel">
                <Zap className="w-3 h-3 text-cyan-400" />
                <span className="text-[10px] text-slate-300">{onlineProviders[0].provider}</span>
              </div>
            )}
          </div>
        </motion.div>

        {/* Orb + quick actions */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="glass-panel p-6 flex flex-col items-center">
          <Orb state={orbState} assistantName={settings?.assistant_name || 'JARVIS'} accentColor={accentColor} size={96} />
          <p className="text-[10px] tracking-[0.4em] text-slate-500 uppercase mt-4 mb-3">Quick Actions</p>
          <div className="flex flex-wrap justify-center gap-2 w-full">
            <QuickActions onAction={onAction} />
          </div>
        </motion.div>

        {/* System snapshot */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="grid grid-cols-3 gap-3">
          {miniStats.map(({ label, value, unit, icon: Icon }) => (
            <div key={label} className="glass-panel p-4 flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <Icon className="w-3.5 h-3.5 text-cyan-400/70" />
                <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">{label}</span>
              </div>
              <div className="text-2xl font-mono text-slate-200">
                {value ?? '--'}
                <span className="text-xs text-slate-500 ml-1">{value !== null ? unit : ''}</span>
              </div>
            </div>
          ))}
        </motion.div>

        {/* Status grid */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button onClick={() => onNavigate('diagnostics')} className="glass-panel p-4 text-left hover:border-cyan-400/30 transition-colors group">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-cyan-400" />
                <span className="text-xs tracking-[0.2em] text-slate-400 uppercase">AI Providers</span>
              </div>
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-400 transition-colors" />
            </div>
            <div className="space-y-1">
              {health?.providers && Object.entries(health.providers).map(([name, p]) => (
                <div key={name} className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 capitalize">{name.replace('_', ' ')}</span>
                  <span className={`flex items-center gap-1 ${p.status === 'online' ? 'text-emerald-400' : 'text-slate-600'}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${p.status === 'online' ? 'bg-emerald-400' : 'bg-slate-700'}`} />
                    {p.status === 'online' ? (p.latency_ms != null ? `${p.latency_ms}ms` : 'online') : 'off'}
                  </span>
                </div>
              ))}
            </div>
          </button>

          <button onClick={() => onNavigate('voice')} className="glass-panel p-4 text-left hover:border-cyan-400/30 transition-colors group">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <AudioLines className="w-4 h-4 text-cyan-400" />
                <span className="text-xs tracking-[0.2em] text-slate-400 uppercase">Voice Engine</span>
              </div>
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-400 transition-colors" />
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between"><span className="text-slate-500">Engine</span><span className="text-slate-300">{voiceInfo?.engine || '—'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Backend</span><span className="text-slate-300">{voiceInfo?.backend || '—'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Voices</span><span className="text-slate-300">{voiceInfo?.catalog?.length || 0}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Microphone</span><span className={voiceInfo?.mic_available ? 'text-emerald-400' : 'text-slate-600'}>{voiceInfo?.mic_available ? 'ready' : 'unavailable'}</span></div>
            </div>
          </button>

          <button onClick={() => onNavigate('coding')} className="glass-panel p-4 text-left hover:border-cyan-400/30 transition-colors group">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-cyan-400" />
                <span className="text-xs tracking-[0.2em] text-slate-400 uppercase">Coding Projects</span>
              </div>
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-400 transition-colors" />
            </div>
            <div className="text-xs">
              <span className="text-slate-300">{projects.length}</span> <span className="text-slate-500">active project{projects.length === 1 ? '' : 's'}</span>
              <div className="mt-1 space-y-0.5">
                {projects.slice(0, 3).map((p) => (
                  <div key={p.name} className="flex justify-between">
                    <span className="text-slate-400">{p.name}</span>
                    <span className="text-slate-600">{fmtTimestamp(p.updated)}</span>
                  </div>
                ))}
              </div>
            </div>
          </button>

          <div className="glass-panel p-4">
            <div className="flex items-center gap-2 mb-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span className="text-xs tracking-[0.2em] text-slate-400 uppercase">System</span>
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between"><span className="text-slate-500">Uptime</span><span className="text-slate-300">{stats?.uptime?.seconds != null ? fmtUptime(stats.uptime.seconds) : '—'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Host</span><span className="text-slate-300 truncate">{stats?.os?.hostname || '—'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Battery</span><span className={stats?.battery?.percent != null ? 'text-slate-300' : 'text-slate-600'}>{stats?.battery?.percent != null ? `${stats.battery.percent}%` : 'N/A'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">WebSocket</span><span className="text-slate-300">{diagnostics?.websocket_clients ?? 0} client(s)</span></div>
            </div>
          </div>
        </motion.div>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="text-[10px] text-slate-600 text-center pb-4">
          Press <span className="text-cyan-400">Ctrl+Space</span> to use voice · <span className="text-cyan-400">Ctrl+Enter</span> to send
        </motion.p>
      </div>
    </div>
  )
}
