import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Zap, Database, Mic, Eye, Cpu, Wifi, Shield, CheckCircle2, AudioLines, Brain } from 'lucide-react'
import { api } from '../../services/api'
import type { DiagnosticInfo, HealthStatus } from '../../types'
import { StartupParticles } from './StartupParticles'
import { ReactorRings } from './ReactorRings'
import { StartupHUD, type HudItem } from './StartupHUD'
import { Orb } from '../Orb/Orb'

interface StartupSequenceProps {
  onComplete: () => void
  accentColor?: string
  assistantName?: string
}

type Phase = 'black' | 'core' | 'rings' | 'diagnostics' | 'widgets' | 'ready'

const DIAGNOSTIC_LINES = [
  'INITIALIZING CORE AI...',
  'LOADING NEURAL NETWORKS...',
  'CALIBRATING ARC REACTOR...',
  'ESTABLISHING SECURE CHANNEL...',
  'VOICE SYSTEM ONLINE...',
  'MEMORY SYSTEM ONLINE...',
  'VISION SYSTEM ONLINE...',
  'ALL SYSTEMS ONLINE',
]

const MAX_DURATION_MS = 5000

function useReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function StartupSequence({ onComplete, accentColor = '#00f0ff', assistantName = 'JARVIS' }: StartupSequenceProps) {
  const [phase, setPhase] = useState<Phase>('black')
  const [progress, setProgress] = useState(0)
  const [diagnosticIndex, setDiagnosticIndex] = useState(0)
  const [hudItems, setHudItems] = useState<HudItem[]>([])
  const [showOrb, setShowOrb] = useState(false)
  const reducedMotion = useReducedMotion()
  const doneRef = useRef(false)
  const onCompleteRef = useRef(onComplete)
  onCompleteRef.current = onComplete

  const displayName = assistantName === 'ALYA' ? 'ALYA' : 'JARVIS'

  useEffect(() => {
    let cancelled = false
    const start = Date.now()

    const finish = () => {
      if (cancelled || doneRef.current) return
      doneRef.current = true
      const elapsed = Date.now() - start
      const wait = Math.max(0, MAX_DURATION_MS - elapsed)
      setTimeout(() => {
        if (cancelled) return
        setPhase('ready')
        setTimeout(() => {
          onCompleteRef.current()
        }, 600)
      }, wait)
    }

    const run = async () => {
      let diag: DiagnosticInfo | null = null
      let health: HealthStatus | null = null
      try {
        health = await api.getHealth()
      } catch {
        // backend unreachable — continue in degraded mode
      }
      try {
        diag = await api.getDiagnostics()
      } catch {
        // diagnostics optional
      }

      // Phase 1: Black → Core ignition (0.5s)
      setPhase('black')
      setProgress(5)
      await new Promise((r) => setTimeout(r, reducedMotion ? 200 : 500))
      if (cancelled) return

      // Phase 2: Core appears (1s)
      setPhase('core')
      setShowOrb(true)
      setProgress(15)
      await new Promise((r) => setTimeout(r, reducedMotion ? 200 : 1000))
      if (cancelled) return

      // Phase 3: Rings assemble (1s)
      setPhase('rings')
      setProgress(30)
      await new Promise((r) => setTimeout(r, reducedMotion ? 200 : 1000))
      if (cancelled) return

      // Phase 4: System diagnostics with typing effect
      setPhase('diagnostics')

      const hudItems: HudItem[] = [
        { id: 'ai_core', label: 'AI CORE', icon: <Brain className="w-3 h-3" />, status: health?.status === 'ok' ? 'online' : 'offline' },
        { id: 'database', label: 'DATABASE', icon: <Database className="w-3 h-3" />, status: diag?.database?.status === 'online' ? 'online' : health?.database?.status === 'online' ? 'online' : 'offline' },
        { id: 'memory', label: 'MEMORY', icon: <Zap className="w-3 h-3" />, status: diag !== null ? 'online' : 'offline' },
        { id: 'microphone', label: 'MICROPHONE', icon: <Mic className="w-3 h-3" />, status: diag?.voice?.mic_available ?? health?.voice?.mic ? 'online' : 'offline' },
        { id: 'tts', label: 'TTS', icon: <AudioLines className="w-3 h-3" />, status: diag?.tts?.available || health?.tts?.status === 'available' ? 'online' : 'offline' },
        { id: 'stt', label: 'STT', icon: <Mic className="w-3 h-3" />, status: (diag?.voice?.mic_available ?? health?.voice?.mic) ? 'online' : 'offline' },
        {
          id: 'local_llm',
          label: 'LOCAL LLM',
          icon: <Cpu className="w-3 h-3" />,
          status: health?.providers?.local_llm?.status === 'online' ? 'online' : health?.providers?.local_llm?.status === 'offline' ? 'offline' : 'warning',
        },
        {
          id: 'groq',
          label: 'GROQ',
          icon: <Brain className="w-3 h-3" />,
          status: health?.providers?.groq?.status === 'online' ? 'online' : health?.providers?.groq?.error ? 'offline' : 'warning',
        },
        {
          id: 'gemini',
          label: 'GEMINI',
          icon: <Brain className="w-3 h-3" />,
          status: health?.providers?.gemini?.status === 'online' ? 'online' : health?.providers?.gemini?.error ? 'offline' : 'warning',
        },
        {
          id: 'openrouter',
          label: 'OPENROUTER',
          icon: <Brain className="w-3 h-3" />,
          status: health?.providers?.openrouter?.status === 'online' ? 'online' : health?.providers?.openrouter?.error ? 'offline' : 'warning',
        },
        { id: 'vision', label: 'VISION', icon: <Eye className="w-3 h-3" />, status: diag?.vision !== undefined ? 'online' : 'warning' },
        { id: 'network', label: 'NETWORK', icon: <Wifi className="w-3 h-3" />, status: 'online' },
        { id: 'security', label: 'SECURITY', icon: <Shield className="w-3 h-3" />, status: 'online' },
      ]
      setHudItems(hudItems)

      for (let i = 0; i < DIAGNOSTIC_LINES.length; i++) {
        if (cancelled) return
        setDiagnosticIndex(i)
        setProgress(35 + i * 8)
        await new Promise((r) => setTimeout(r, reducedMotion ? 80 : 200))
      }
      if (cancelled) return

      // Phase 5: Widgets reveal
      setPhase('widgets')
      setProgress(100)
      await new Promise((r) => setTimeout(r, reducedMotion ? 200 : 800))
      if (cancelled) return

      finish()
    }

    run()
    return () => {
      cancelled = true
    }
  }, [onComplete, accentColor, reducedMotion])

  const glowColor = accentColor

  const renderCore = () => (
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
      <motion.div
        initial={{ opacity: 0, scale: 0.7 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: reducedMotion ? 0.2 : 0.8, ease: 'easeOut' }}
        className="relative"
        style={{ filter: `drop-shadow(0 0 24px ${glowColor}60)` }}
      >
        {showOrb && (
          <Orb
            state="idle"
            assistantName={displayName}
            accentColor={glowColor}
            size={80}
          />
        )}
      </motion.div>

      <motion.div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full"
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 0.5, scale: 1.4 }}
        transition={{ duration: 1.4, repeat: Infinity, repeatType: 'reverse' }}
        style={{
          width: 90,
          height: 90,
          background: `radial-gradient(circle, ${glowColor} 0%, transparent 70%)`,
          filter: 'blur(8px)',
        }}
      />
    </div>
  )

  const renderDiagnostics = () => (
    <div className="absolute bottom-20 left-0 right-0 flex flex-col items-center">
      <div className="h-40 flex flex-col items-center justify-center gap-1.5 overflow-hidden">
        {DIAGNOSTIC_LINES.slice(0, diagnosticIndex + 1).map((line, i) => (
          <motion.div
            key={i}
            className="text-xs font-mono flex items-center gap-2"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: reducedMotion ? 0.05 : 0.15 }}
            style={{ color: i === diagnosticIndex ? glowColor : '#94a3b8' }}
          >
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: i === diagnosticIndex ? glowColor : '#475569' }} />
            <span className="typing">{line}</span>
          </motion.div>
        ))}
      </div>

      <motion.div
        className="w-48 h-0.5 bg-slate-800 rounded-full overflow-hidden mt-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <motion.div
          className="h-full rounded-full"
          style={{
            background: `linear-gradient(90deg, ${glowColor}, ${glowColor}60 100%)`,
            width: `${progress}%`,
          }}
          transition={{ duration: 0.3 }}
        />
      </motion.div>
    </div>
  )

  return (
    <motion.div
      className="fixed inset-0 z-[100] flex items-center justify-center overflow-hidden"
      style={{
        background: phase === 'black' ? '#000000' : '#02060c',
      }}
      exit={{ opacity: 0, scale: 1.04 }}
      transition={{ duration: 0.6, ease: 'easeInOut' }}
    >
      {!reducedMotion && <StartupParticles accentColor={glowColor} />}
      {phase !== 'black' && <ReactorRings accentColor={glowColor} stage={phase === 'diagnostics' || phase === 'widgets' ? 'complete' : phase === 'rings' ? 'active' : 'starting'} reducedMotion={reducedMotion} />}
      {(phase === 'diagnostics' || phase === 'widgets') && <StartupHUD items={hudItems} accentColor={glowColor} />}

      {phase === 'core' || phase === 'rings' || phase === 'diagnostics' || phase === 'widgets' ? (
        renderCore()
      ) : (
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reducedMotion ? 0.1 : 0.6 }}
        >
        </motion.div>
      )}

      {(phase === 'diagnostics' || phase === 'widgets') && renderDiagnostics()}

      <AnimatePresence>
        {phase === 'ready' && (
          <motion.div
            className="absolute bottom-10 text-xs font-mono"
            style={{ color: glowColor }}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <div className="flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" />
              <span>ALL SYSTEMS ONLINE</span>
            </div>
            <div className="text-[10px] mt-1 opacity-50">
              Assalamualaikum. {displayName} ready hai.
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        .typing {
          overflow: hidden;
          border-right: 1px solid ${glowColor}80;
          padding-right: 4px;
          white-space: nowrap;
          animation: typing 0.8s steps(30, end), caret 0.7s step-end infinite;
        }
        @keyframes typing {
          from { width: 0; }
          to { width: 100%; }
        }
        @keyframes caret {
          0%, 100% { border-color: transparent; }
          50% { border-color: ${glowColor}80; }
        }
        @media (prefers-reduced-motion: reduce) {
          .typing {
            animation: none;
            border: none;
          }
        }
      `}</style>
    </motion.div>
  )
}
