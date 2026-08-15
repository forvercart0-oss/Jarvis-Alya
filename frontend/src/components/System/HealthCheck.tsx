import type { HealthStatus } from '../../types'
import { Wifi, Mic, Database, Radio } from 'lucide-react'

interface HealthCheckProps {
  health: HealthStatus | null
}

export function HealthCheck({ health }: HealthCheckProps) {
  if (!health) {
    return (
      <div className="text-center text-slate-500 py-10">Loading health status...</div>
    )
  }

  const providerEntries = Object.entries(health.providers)

  const items: { key: string; label: string; icon: React.ReactNode; data: { status: string; error?: string; model?: string; url?: string } }[] = [
    ...providerEntries.map(([key, data]) => ({
      key,
      label: key.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
      icon: <Radio className="w-4 h-4" />,
      data: data as { status: string; error?: string; model?: string; url?: string },
    })),
    { key: 'tts', label: 'TTS Engine', icon: <Mic className="w-4 h-4" />, data: health.tts },
    { key: 'voice', label: 'Voice', icon: <Mic className="w-4 h-4" />, data: health.voice },
    { key: 'database', label: 'Database', icon: <Database className="w-4 h-4" />, data: health.database },
    { key: 'websocket', label: 'WebSocket', icon: <Wifi className="w-4 h-4" />, data: health.websocket },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {items.map(({ key, label, icon, data }) => (
        <div key={key} className="glass-panel p-3 flex items-center gap-3">
          <div className="text-slate-400">{icon}</div>
          <div className="flex-1 min-w-0">
            <div className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">{label}</div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`text-xs font-medium ${getStatusColor(data.status)}`}>{data.status}</span>
              {data.error && <span className="text-[10px] text-red-400 truncate">{data.error}</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function getStatusColor(status: string) {
  if (status === 'healthy' || status === 'online') return 'text-green-400'
  if (status === 'degraded') return 'text-yellow-400'
  return 'text-red-400'
}
