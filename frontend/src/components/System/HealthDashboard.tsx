import { useState, useEffect } from 'react'
import { Activity, Cpu, Mic, Camera, MessageSquare, Phone, ImageIcon, VideoIcon } from 'lucide-react'
import { api } from '../../services/api'

interface HealthDashboardProps {
  health: any
  diagnostics: any
}

interface ProviderCardProps {
  title: string
  icon: React.ReactNode
  status: string
  detail?: string
  color: string
}

function ProviderCard({ title, icon, status, detail, color }: ProviderCardProps) {
  const isOnline = status === 'online' || status === 'available' || status === 'ready'
  const isConfigured = status !== 'not_configured' && status !== 'unavailable'

  return (
    <div className="glass-panel p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isOnline ? 'bg-green-500/10' : isConfigured ? 'bg-yellow-500/10' : 'bg-slate-800/50'}`}>
            {icon}
          </div>
          <div>
            <div className="text-xs text-slate-300">{title}</div>
            {detail && <div className="text-[10px] text-slate-500">{detail}</div>}
          </div>
        </div>
        <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.6)]' : isConfigured ? 'bg-yellow-400 animate-pulse' : 'bg-slate-600'}`} />
      </div>
      <div className={`text-[10px] tracking-wider uppercase ${isOnline ? 'text-green-400' : isConfigured ? 'text-yellow-400' : 'text-slate-500'}`}>
        {isOnline ? 'ONLINE' : isConfigured ? 'CHECKING' : status.toUpperCase()}
      </div>
    </div>
  )
}

export function HealthDashboard({ health, diagnostics }: HealthDashboardProps) {
  const [refreshing, setRefreshing] = useState(false)

  const refresh = async () => {
    setRefreshing(true)
    try {
      await Promise.all([
        api.getHealth(),
        api.getDiagnostics(),
      ])
    } catch {
      // ignore
    } finally {
      setRefreshing(false)
    }
  }

  const providers = health?.providers || {}
  const imageProviders = diagnostics?.image || {}
  const videoProviders = diagnostics?.video || {}

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-500/10">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm tracking-[0.2em] text-cyan-400/70 uppercase">Provider Health</h2>
        </div>
        <button
          onClick={refresh}
          disabled={refreshing}
          className="text-[10px] tracking-widest text-slate-500 hover:text-cyan-300 transition-colors uppercase"
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div>
          <h3 className="text-[10px] tracking-[0.25em] uppercase text-slate-500 mb-2">Text AI</h3>
          <div className="grid grid-cols-2 gap-2">
            <ProviderCard
              title="Groq"
              icon={<Cpu className="w-4 h-4 text-cyan-400" />}
              status={providers?.groq?.status || 'unknown'}
              detail={providers?.groq?.model || ''}
              color="#00f0ff"
            />
            <ProviderCard
              title="Local AI"
              icon={<Cpu className="w-4 h-4 text-violet-400" />}
              status={providers?.local_llm?.status || 'unknown'}
              detail={providers?.local_llm?.url || ''}
              color="#a855f7"
            />
            <ProviderCard
              title="Gemini"
              icon={<Cpu className="w-4 h-4 text-blue-400" />}
              status={providers?.gemini?.status || 'unknown'}
              detail={providers?.gemini?.model || ''}
              color="#3b82f6"
            />
            <ProviderCard
              title="OpenRouter"
              icon={<Cpu className="w-4 h-4 text-green-400" />}
              status={providers?.openrouter?.status || 'unknown'}
              detail={providers?.openrouter?.model || ''}
              color="#22c55e"
            />
          </div>
        </div>

        <div>
          <h3 className="text-[10px] tracking-[0.25em] uppercase text-slate-500 mb-2">Voice</h3>
          <div className="grid grid-cols-2 gap-2">
            <ProviderCard
              title="TTS"
              icon={<MessageSquare className="w-4 h-4 text-pink-400" />}
              status={health?.tts?.status || 'unknown'}
              detail={health?.tts?.engine || ''}
              color="#ec4899"
            />
            <ProviderCard
              title="STT"
              icon={<Mic className="w-4 h-4 text-orange-400" />}
              status={health?.voice?.status || 'unknown'}
              detail={health?.voice?.mic ? 'Microphone ready' : 'No microphone'}
              color="#f97316"
            />
          </div>
        </div>

        <div>
          <h3 className="text-[10px] tracking-[0.25em] uppercase text-slate-500 mb-2">Media Generation</h3>
          <div className="grid grid-cols-2 gap-2">
            <ProviderCard
              title="Image"
              icon={<ImageIcon className="w-4 h-4 text-purple-400" />}
              status={Object.keys(imageProviders).length > 0 ? 'online' : 'not_configured'}
              detail={Object.keys(imageProviders).join(', ') || 'No providers'}
              color="#a855f7"
            />
            <ProviderCard
              title="Video"
              icon={<VideoIcon className="w-4 h-4 text-red-400" />}
              status={Object.keys(videoProviders).length > 0 ? 'online' : 'not_configured'}
              detail={Object.keys(videoProviders).join(', ') || 'No providers'}
              color="#ef4444"
            />
          </div>
        </div>

        <div>
          <h3 className="text-[10px] tracking-[0.25em] uppercase text-slate-500 mb-2">System</h3>
          <div className="grid grid-cols-2 gap-2">
            <ProviderCard
              title="Gestures"
              icon={<Camera className="w-4 h-4 text-teal-400" />}
              status={diagnostics?.gestures?.active ? 'active' : 'inactive'}
              detail={diagnostics?.gestures?.available ? 'Camera ready' : 'Not configured'}
              color="#14b8a6"
            />
            <ProviderCard
              title="Calls"
              icon={<Phone className="w-4 h-4 text-indigo-400" />}
              status={diagnostics?.calls?.available ? 'available' : 'not_configured'}
              detail={diagnostics?.calls?.provider || 'No provider'}
              color="#6366f1"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
