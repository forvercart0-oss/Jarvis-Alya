import { useEffect, useState } from 'react'
import { Cpu, Heart, Zap, Server, ShieldCheck } from 'lucide-react'
import type { DiagnosticInfo } from '../../types'
import { api } from '../../services/api'

function fmtUptime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

const STACK = [
  { name: 'Python / FastAPI', role: 'Core backend · WebSocket · tools', icon: Server },
  { name: 'React / Vite / TypeScript', role: 'Frontend shell', icon: Zap },
  { name: 'Groq / Gemini / OpenRouter', role: 'AI providers with auto-failover', icon: Cpu },
  { name: 'Kokoro · eSpeak-ng', role: 'Neural TTS with graceful fallback', icon: Heart },
  { name: 'Tauri (desktop)', role: 'Native window shell', icon: ShieldCheck },
]

export function AboutPanel() {
  const [diag, setDiag] = useState<DiagnosticInfo | null>(null)

  useEffect(() => {
    api.getDiagnostics().then(setDiag).catch(() => null)
  }, [])

  return (
    <div className="h-full overflow-y-auto p-6 max-w-2xl mx-auto">
      <div className="flex flex-col items-center text-center mb-8">
        <svg viewBox="0 0 64 64" className="w-24 h-24 mb-4 drop-shadow-[0_0_28px_rgba(0,240,255,0.4)]">
          <defs>
            <linearGradient id="aboutGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#00f0ff" />
              <stop offset="100%" stopColor="#0077ff" />
            </linearGradient>
          </defs>
          <polygon points="32,6 55,19 55,45 32,58 9,45 9,19" fill="none" stroke="url(#aboutGrad)" strokeWidth="2.5" strokeLinejoin="round" />
          <circle cx="32" cy="32" r="5" fill="#00f0ff" />
        </svg>
        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-500 tracking-widest">
          JARVIS 2.0
        </h1>
        <p className="text-xs text-slate-500 mt-2 tracking-[0.3em] uppercase">Your Intelligent Desktop Assistant</p>

        {diag && (
          <div className="flex gap-3 mt-4">
            <span className="glass-panel px-3 py-1 text-[10px] text-cyan-400 font-mono">v{diag.version}</span>
            <span className="glass-panel px-3 py-1 text-[10px] text-slate-400 font-mono">Python {diag.python}</span>
            <span className="glass-panel px-3 py-1 text-[10px] text-slate-400 font-mono">Uptime {fmtUptime(diag.uptime_seconds)}</span>
          </div>
        )}
      </div>

      <div className="glass-panel p-4 mb-4">
        <h3 className="text-xs tracking-[0.2em] text-cyan-400/70 uppercase mb-2">Built with</h3>
        <div className="space-y-2">
          {STACK.map(({ name, role, icon: Icon }) => (
            <div key={name} className="flex items-center gap-3">
              <Icon className="w-4 h-4 text-cyan-400/60 shrink-0" />
              <div>
                <div className="text-xs text-slate-300">{name}</div>
                <div className="text-[10px] text-slate-500">{role}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-panel p-4 mb-4">
        <h3 className="text-xs tracking-[0.2em] text-cyan-400/70 uppercase mb-2">Capabilities</h3>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-slate-400 list-disc pl-4">
          <li>Natural-language system control</li>
          <li>Multi-provider AI with auto-failover</li>
          <li>Wake-word voice input ("Hey JARVIS")</li>
          <li>Neural TTS with live voice picker</li>
          <li>Full-stack project builder & coding agent</li>
          <li>Scoped, safety-checked terminal access</li>
          <li>Persistent conversation memory</li>
          <li>Live system monitoring & screenshots</li>
          <li>Automations & web search</li>
          <li>Native desktop shell (Tauri)</li>
        </ul>
      </div>

      <div className="text-center text-[10px] text-slate-600 pb-6">
        <p>Running on {diag?.os?.name || 'Linux'} · {diag?.os?.kernel || ''}</p>
        <p className="mt-1">Crafted with care for a smarter desktop.</p>
      </div>
    </div>
  )
}
