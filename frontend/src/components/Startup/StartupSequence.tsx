import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../../services/api'
import type { DiagnosticInfo, HealthStatus } from '../../types'

interface StartupSequenceProps {
  onComplete: () => void
}

interface BootStep {
  id: string
  label: string
  status: 'pending' | 'running' | 'ok' | 'warn' | 'fail'
  detail?: string
}

const MIN_DURATION_MS = 3600

function stepDuration(i: number) {
  return 200 + Math.sin(i * 2.7) * 50
}

export function StartupSequence({ onComplete }: StartupSequenceProps) {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<'booting' | 'ready' | 'error'>('booting')
  const [steps, setSteps] = useState<BootStep[]>([
    { id: 'ai_core', label: 'AI CORE', status: 'pending' },
    { id: 'database', label: 'DATABASE', status: 'pending' },
    { id: 'memory', label: 'MEMORY', status: 'pending' },
    { id: 'microphone', label: 'MICROPHONE', status: 'pending' },
    { id: 'kokoro_tts', label: 'KOKORO TTS', status: 'pending' },
    { id: 'pipewire', label: 'PIPEWIRE', status: 'pending' },
    { id: 'system_tools', label: 'SYSTEM TOOLS', status: 'pending' },
    { id: 'groq', label: 'GROQ', status: 'pending' },
    { id: 'local_ai', label: 'LOCAL AI', status: 'pending' },
    { id: 'gemini', label: 'GEMINI', status: 'pending' },
    { id: 'openrouter', label: 'OPENROUTER', status: 'pending' },
  ])
  const doneRef = useRef(false)

  const setStep = (id: string, patch: Partial<BootStep>) => {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, ...patch } : s)))
  }

  useEffect(() => {
    let cancelled = false
    const start = Date.now()

    const finish = (ok: boolean) => {
      if (cancelled || doneRef.current) return
      doneRef.current = true
      const elapsed = Date.now() - start
      const wait = Math.max(0, MIN_DURATION_MS - elapsed)
      setTimeout(() => {
        if (cancelled) return
        if (ok) {
          setStatus('ready')
          setTimeout(onComplete, 500)
        } else {
          setStatus('error')
          setTimeout(onComplete, 800)
        }
      }, wait)
    }

    const run = async () => {
      let diag: DiagnosticInfo | null = null
      let health: HealthStatus | null = null
      try {
        health = await api.getHealth()
      } catch {
        /* unreachable backend handled below */
      }
      try {
        diag = await api.getDiagnostics()
      } catch {
        /* diagnostics optional */
      }

      const mark = (id: string, ok: boolean, detail: string, weight: number, waitMs: number) => {
        setStep(id, { status: ok ? 'ok' : 'warn', detail })
        setProgress((p) => Math.min(98, p + weight))
        return new Promise((r) => setTimeout(r, waitMs))
      }

      // AI CORE
      setStep('ai_core', { status: 'running', detail: 'initializing' })
      await new Promise((r) => setTimeout(r, stepDuration(0)))
      if (!health || health.status !== 'ok') {
        setStep('ai_core', { status: 'fail', detail: 'backend unreachable' })
        setStatus('error')
        setTimeout(onComplete, 700)
        return
      }
      await mark('ai_core', true, health.assistant ? `${health.assistant} core online` : 'online', 8, stepDuration(0))

      // DATABASE
      const dbOnline = diag?.database?.status === 'online' || health?.database?.status === 'online'
      await mark('database', dbOnline, dbOnline ? 'sqlite ready' : 'offline', 8, stepDuration(1))

      // MEMORY
      const conversations = diag?.memory?.conversations ?? 0
      await mark('memory', diag !== null, `${conversations} conversation${conversations === 1 ? '' : 's'}`, 8, stepDuration(2))

      // MICROPHONE
      const micOk = diag?.voice?.mic_available ?? health?.voice?.mic ?? false
      await mark('microphone', micOk, micOk ? 'input ready' : 'not detected', 8, stepDuration(3))

      // KOKORO TTS
      const ttsOk = diag?.tts?.available ?? health?.tts?.status === 'available'
      const ttsBackend = diag?.tts?.backend ?? health?.tts?.backend ?? 'none'
      const ttsEngine = diag?.tts?.engine ?? health?.tts?.engine ?? 'espeak'
      await mark('kokoro_tts', ttsOk, ttsOk ? `${ttsBackend} · ${ttsEngine}` : 'fallback to espeak', 10, stepDuration(4))

      // PIPEWIRE
      const pwOk = diag?.pipewire?.status === 'online'
      await mark('pipewire', pwOk, pwOk ? 'audio server ready' : 'offline', 8, stepDuration(5))

      // SYSTEM TOOLS
      const tools = diag?.tools ?? 0
      await mark('system_tools', tools > 0, `${tools} registered`, 8, stepDuration(6))

      // Provider checks
      const providers = diag?.providers ?? health?.providers ?? {}
      const pv = (name: string) => providers[name]
      const markProvider = async (id: string, _label: string, name: string, weight: number, i: number) => {
        const p = pv(name)
        const online = p?.status === 'online'
        const detail = online
          ? p?.latency_ms != null ? `${p.model ?? name} · ${p.latency_ms}ms` : `${p.model ?? name} · online`
          : p?.error ?? 'not configured'
        await mark(id, online, detail, weight, stepDuration(i))
      }

      await markProvider('groq', 'GROQ', 'groq', 9, 7)
      await markProvider('local_ai', 'LOCAL AI', 'local_llm', 9, 8)
      await markProvider('gemini', 'GEMINI', 'gemini', 9, 9)
      await markProvider('openrouter', 'OPENROUTER', 'openrouter', 9, 10)

      setProgress(100)
      finish(true)
    }

    run()
    return () => {
      cancelled = true
    }
  }, [onComplete])

  return (
    <motion.div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-[#02060c]"
      exit={{ opacity: 0, scale: 1.04 }}
      transition={{ duration: 0.6, ease: 'easeInOut' }}
    >
      <div className="w-full max-w-md px-8">
        {/* Core logo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7 }}
          className="flex flex-col items-center mb-10"
        >
          <svg viewBox="0 0 64 64" className="w-20 h-20 mb-4 drop-shadow-[0_0_24px_rgba(0,240,255,0.45)]">
            <defs>
              <linearGradient id="bootGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00f0ff" />
                <stop offset="100%" stopColor="#0077ff" />
              </linearGradient>
            </defs>
            <polygon points="32,6 55,19 55,45 32,58 9,45 9,19" fill="none" stroke="url(#bootGrad)" strokeWidth="2.5" strokeLinejoin="round" />
            <circle cx="32" cy="32" r="5" fill="#00f0ff">
              <animate attributeName="opacity" values="1;0.3;1" dur="1.6s" repeatCount="indefinite" />
            </circle>
          </svg>
          <motion.h1
            initial={{ letterSpacing: '0.6em', opacity: 0 }}
            animate={{ letterSpacing: '0.35em', opacity: 1 }}
            transition={{ duration: 1 }}
            className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-500"
          >
            JARVIS 2.0
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-[10px] tracking-[0.5em] text-cyan-500/60 mt-2 uppercase"
          >
            Artificial Intelligence
          </motion.p>
        </motion.div>

        {/* Boot steps */}
        <div className="space-y-1.5 mb-8">
          {steps.map((step, i) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
              className="flex items-center gap-3 text-[11px] font-mono"
            >
              <div className="w-4 flex justify-center">
                {step.status === 'running' && (
                  <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                )}
                {step.status === 'ok' && <span className="text-emerald-400">&#10003;</span>}
                {step.status === 'warn' && <span className="text-yellow-400">&#9888;</span>}
                {step.status === 'fail' && <span className="text-red-400">&#10005;</span>}
                {step.status === 'pending' && <span className="w-1.5 h-1.5 rounded-full bg-slate-700" />}
              </div>
              <span className={step.status === 'pending' ? 'text-slate-600' : 'text-slate-300'}>{step.label}</span>
              {step.detail && <span className="ml-auto text-slate-500 text-[10px]">{step.detail}</span>}
            </motion.div>
          ))}
        </div>

        {/* Progress bar */}
        <div className="h-[2px] bg-slate-800 rounded overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-cyan-400 to-blue-500"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4 }}
          />
        </div>

        <AnimatePresence>
          {status === 'ready' && (
            <motion.p
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center text-[10px] tracking-[0.4em] text-emerald-400/80 uppercase mt-4"
            >
              All systems nominal
            </motion.p>
          )}
          {status === 'error' && (
            <motion.p
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center text-[10px] tracking-[0.4em] text-red-400/80 uppercase mt-4"
            >
              Backend unreachable — continuing in degraded mode
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
