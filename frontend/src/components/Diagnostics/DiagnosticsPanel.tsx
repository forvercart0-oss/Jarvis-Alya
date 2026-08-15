import { useEffect, useState } from 'react'
import { RefreshCw, Server, Database, AudioLines, Mic, Cpu, Wifi, Boxes } from 'lucide-react'
import type { DiagnosticInfo } from '../../types'
import { api } from '../../services/api'
import { Button } from '../Common/Button'

function fmtUptime(seconds: number) {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return d > 0 ? `${d}d ${h}h ${m}m` : `${h}h ${m}m`
}

function ProviderRow({ name, status }: { name: string; status: any }) {
  const state = status?.status
  const dot = state === 'online' ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]' : state === 'offline' ? 'bg-slate-700' : 'bg-yellow-400'
  return (
    <div className="flex items-center justify-between px-3 py-2 rounded bg-slate-900/40">
      <div className="flex items-center gap-2.5">
        <span className={`w-2 h-2 rounded-full ${dot}`} />
        <span className="text-xs text-slate-300 capitalize">{name.replace('_', ' ')}</span>
      </div>
      <div className="text-[10px] text-slate-500 text-right">
        {state === 'online' && status.latency_ms != null && <span>{status.latency_ms}ms · </span>}
        {status.model && <span className="block max-w-[220px] truncate">{status.model}</span>}
        {state !== 'online' && status.error && <span className="block max-w-[220px] truncate">{status.error}</span>}
        {state === 'offline' && !status.error && <span>offline</span>}
      </div>
    </div>
  )
}

export function DiagnosticsPanel() {
  const [diag, setDiag] = useState<DiagnosticInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    try {
      setDiag(await api.getDiagnostics())
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load diagnostics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const timer = setInterval(load, 5000)
    return () => clearInterval(timer)
  }, [])

  if (loading && !diag) {
    return <div className="h-full flex items-center justify-center text-slate-500 text-xs">Running diagnostics...</div>
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase">System Diagnostics</h3>
        <Button size="sm" variant="secondary" onClick={load} disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {error && <div className="glass-panel p-3 text-xs text-red-400">{error}</div>}

      {diag && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Version', value: diag.version, icon: Server },
              { label: 'Uptime', value: fmtUptime(diag.uptime_seconds), icon: Cpu },
              { label: 'Tools', value: String(diag.tools), icon: Boxes },
              { label: 'WS Clients', value: String(diag.websocket_clients), icon: Wifi },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="glass-panel p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Icon className="w-3.5 h-3.5 text-cyan-400/70" />
                  <span className="text-[10px] tracking-[0.2em] text-slate-500 uppercase">{label}</span>
                </div>
                <div className="text-lg font-mono text-slate-200 truncate">{value}</div>
              </div>
            ))}
          </div>

          <div className="glass-panel p-3">
            <h4 className="text-xs tracking-[0.2em] text-slate-500 uppercase mb-2">AI Providers</h4>
            <div className="space-y-1.5">
              {diag.providers && Object.entries(diag.providers).map(([name, status]) => (
                <ProviderRow key={name} name={name} status={status} />
              ))}
            </div>
            {diag.active_provider && (
              <div className="mt-2 text-[11px] text-cyan-400/80">
                Active provider: <span className="font-mono">{diag.active_provider}</span>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="glass-panel p-3">
              <h4 className="text-xs tracking-[0.2em] text-slate-500 uppercase mb-2">Voice & TTS</h4>
              <div className="space-y-1.5 text-xs">
                <Row label="TTS Engine" value={diag.tts.engine} />
                <Row label="Backend" value={diag.tts.backend || 'none'} />
                <Row label="Available voices" value={String(diag.tts.voices)} />
                <Row label="Current voice" value={diag.tts.voice} />
                <Row label="Microphone" value={diag.voice.mic_available ? 'ready' : 'unavailable'} ok={diag.voice.mic_available} />
              </div>
            </div>

            <div className="glass-panel p-3">
              <h4 className="text-xs tracking-[0.2em] text-slate-500 uppercase mb-2">Core Services</h4>
              <div className="space-y-1.5 text-xs">
                <ServiceRow label="Database" icon={Database} status={diag.database?.status} />
                <ServiceRow label="WebSocket" icon={Wifi} status={diag.websocket?.status} />
                <ServiceRow label="Voice init" icon={Mic} status={diag.voice.initialized ? 'online' : 'offline'} />
                <ServiceRow label="TTS" icon={AudioLines} status={diag.tts.available ? 'online' : 'offline'} />
                <div className="flex justify-between pt-1"><span className="text-slate-500">Python</span><span className="text-slate-300 font-mono">{diag.python}</span></div>
              </div>
            </div>
          </div>

          <div className="glass-panel p-3 text-xs">
            <h4 className="text-[10px] tracking-[0.2em] text-slate-500 uppercase mb-2">Machine</h4>
            <div className="space-y-1">
              <Row label="Hostname" value={diag.os.hostname || '—'} />
              <Row label="OS" value={diag.os.name || '—'} />
              <Row label="Kernel" value={diag.os.kernel || '—'} />
              <Row label="Memory DB" value={`${diag.memory?.conversations ?? 0} conversations`} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function Row({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-500">{label}</span>
      <span className={ok === undefined ? 'text-slate-300' : ok ? 'text-emerald-400' : 'text-slate-600'}>{value}</span>
    </div>
  )
}

function ServiceRow({ label, icon: Icon, status }: { label: string; icon: any; status?: string }) {
  const ok = status === 'online' || status === 'ok'
  return (
    <div className="flex items-center justify-between">
      <span className="flex items-center gap-2 text-slate-500">
        <Icon className="w-3.5 h-3.5" />
        {label}
      </span>
      <span className={`flex items-center gap-1.5 text-[10px] uppercase tracking-wider ${ok ? 'text-emerald-400' : 'text-red-400'}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-emerald-400' : 'bg-red-400'}`} />
        {ok ? 'online' : status || 'offline'}
      </span>
    </div>
  )
}
