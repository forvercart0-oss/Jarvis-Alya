import { useEffect, useState } from 'react'
import type { SystemStats, HealthStatus } from '../../types'
import { Cpu, HardDrive, Battery, Activity, RefreshCw, Radio, Mic, Database, Wifi } from 'lucide-react'
import { StatCard } from './StatCard'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface SystemPanelProps {
  stats: SystemStats | null
  health: HealthStatus | null
}

export function SystemPanel({ stats, health }: SystemPanelProps) {
  const [history, setHistory] = useState<{ cpu: any[]; ram: any[] }>({ cpu: [], ram: [] })
  const [refreshing, setRefreshing] = useState(false)

  const fetchHistory = async () => {
    try {
      const data = await fetch('/api/system/history').then(r => r.json())
      setHistory(data)
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    fetchHistory()
    const timer = setInterval(fetchHistory, 2000)
    return () => clearInterval(timer)
  }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchHistory()
    setRefreshing(false)
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase">System Resources</h3>
        <button onClick={handleRefresh} className="text-slate-500 hover:text-cyan-300 transition-colors">
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <StatCard title="CPU" value={stats?.cpu.percent ?? null} unit="%" icon={<Cpu className="w-5 h-5" />} error={stats?.cpu.error} />
        <StatCard title="RAM" value={stats?.ram.percent ?? null} unit="%" icon={<Activity className="w-5 h-5" />} error={stats?.ram.error} />
        <StatCard title="Disk" value={stats?.disk.percent ?? null} unit="%" icon={<HardDrive className="w-5 h-5" />} error={stats?.disk.error} />
        {stats?.battery.present && (
          <StatCard title="Battery" value={stats.battery.percent ?? null} unit="%" icon={<Battery className="w-5 h-5" />} error={stats.battery.error} />
        )}
      </div>

      <div className="glass-panel p-3">
        <h4 className="text-xs tracking-[0.2em] text-slate-500 uppercase mb-2">CPU Usage</h4>
        <div className="h-24">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history.cpu}>
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 100]} hide />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(0,240,255,0.2)', borderRadius: '4px' }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Line type="monotone" dataKey="value" stroke="#00f0ff" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-panel p-3">
        <h4 className="text-xs tracking-[0.2em] text-slate-500 uppercase mb-2">RAM Usage</h4>
        <div className="h-24">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history.ram}>
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 100]} hide />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(0,240,255,0.2)', borderRadius: '4px' }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Line type="monotone" dataKey="value" stroke="#a855f7" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {stats?.uptime.seconds !== undefined && stats?.uptime.seconds !== null && (
        <div className="glass-panel p-3 flex items-center justify-between">
          <span className="text-xs tracking-[0.2em] text-slate-500 uppercase">Uptime</span>
          <span className="text-sm text-cyan-400 font-mono">
            {Math.floor(stats.uptime.seconds / 3600)}h {Math.floor((stats.uptime.seconds % 3600) / 60)}m
          </span>
        </div>
      )}

      {stats?.os && (
        <div className="glass-panel p-3">
          <h4 className="text-xs tracking-[0.2em] text-slate-500 uppercase mb-2">Operating System</h4>
          <div className="space-y-1 text-xs">
            {stats.os.name && <div className="flex justify-between"><span className="text-slate-500">OS</span><span className="text-slate-300">{stats.os.name}</span></div>}
            {stats.os.version && <div className="flex justify-between"><span className="text-slate-500">Version</span><span className="text-slate-300">{stats.os.version}</span></div>}
            {stats.os.kernel && <div className="flex justify-between"><span className="text-slate-500">Kernel</span><span className="text-slate-300">{stats.os.kernel}</span></div>}
            {stats.os.hostname && <div className="flex justify-between"><span className="text-slate-500">Host</span><span className="text-slate-300">{stats.os.hostname}</span></div>}
          </div>
        </div>
      )}

      {health && (
        <div>
          <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-3">Service Health</h3>
          <div className="space-y-2">
            {Object.entries(health).map(([key, val]) => (
              <div key={key} className="glass-panel p-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {key === 'groq' && <Radio className="w-4 h-4 text-slate-400" />}
                  {key === 'local_llm' && <Cpu className="w-4 h-4 text-slate-400" />}
                  {key === 'tts' && <Mic className="w-4 h-4 text-slate-400" />}
                  {key === 'voice' && <Mic className="w-4 h-4 text-slate-400" />}
                  {key === 'database' && <Database className="w-4 h-4 text-slate-400" />}
                  {key === 'websocket' && <Wifi className="w-4 h-4 text-slate-400" />}
                  <span className="text-xs text-slate-400 capitalize">{key.replace('_', ' ')}</span>
                </div>
                <div className="flex items-center gap-2">
                  {val.model && <span className="text-[10px] text-slate-500">{val.model}</span>}
                  {val.url && <span className="text-[10px] text-slate-500 truncate max-w-[150px]">{val.url}</span>}
                  <StatusBadge status={val.status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const color = status === 'healthy' || status === 'online' ? 'text-green-400 bg-green-400/10' : status === 'degraded' ? 'text-yellow-400 bg-yellow-400/10' : 'text-red-400 bg-red-400/10'
  return <span className={`text-[10px] px-2 py-0.5 rounded uppercase tracking-wider ${color}`}>{status}</span>
}
