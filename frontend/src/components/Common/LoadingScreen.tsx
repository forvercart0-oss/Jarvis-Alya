import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, Loader2 } from 'lucide-react'
import { LoadingSpinner } from './LoadingSpinner'

interface LoadingScreenProps {
  onComplete: () => void
}

const SERVICES = [
  { name: 'API Gateway', key: 'api' },
  { name: 'WebSocket', key: 'ws' },
  { name: 'AI Engine', key: 'ai' },
  { name: 'TTS Engine', key: 'tts' },
  { name: 'Memory Bank', key: 'memory' },
  { name: 'System Monitor', key: 'system' },
]

export function LoadingScreen({ onComplete }: LoadingScreenProps) {
  const [ready, setReady] = useState(false)
  const [checks, setChecks] = useState<Record<string, boolean>>({})

  useEffect(() => {
    let completed = 0
    const total = SERVICES.length

    SERVICES.forEach((svc, idx) => {
      setTimeout(() => {
        setChecks((prev) => ({ ...prev, [svc.key]: true }))
        completed++
        if (completed === total) {
          setTimeout(() => {
            setReady(true)
            setTimeout(onComplete, 800)
          }, 600)
        }
      }, 400 + idx * 300)
    })
  }, [onComplete])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-jarvis-dark">
      <div className="text-center space-y-8">
        <div className="flex flex-col items-center gap-4">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <svg viewBox="0 0 80 80" className="w-20 h-20 text-cyan-400">
              <path d="M40 10 L70 25 L70 55 L40 70 L10 55 L10 25 Z" fill="none" stroke="currentColor" strokeWidth="2" />
              <path d="M40 10 L40 70 M10 25 L70 55 M70 25 L10 55" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.5" />
              <circle cx="40" cy="40" r="8" fill="currentColor" opacity="0.3" />
            </svg>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <h1 className="text-4xl font-bold glow-text text-cyan-400 tracking-[0.3em]">JARVIS</h1>
            <p className="text-xs text-slate-400 tracking-[0.4em] uppercase mt-1">Version 2.0</p>
          </motion.div>
        </div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="space-y-3">
          <p className="text-xs tracking-[0.3em] text-slate-500 uppercase">Initializing System</p>
          <div className="flex justify-center">
            <LoadingSpinner size={32} />
          </div>
          <div className="space-y-1.5">
            {SERVICES.map((svc) => (
              <motion.div
                key={svc.key}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 }}
                className="flex items-center justify-center gap-2 text-xs"
              >
                {checks[svc.key] ? (
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                ) : (
                  <Loader2 className="w-4 h-4 text-slate-600 animate-spin" />
                )}
                <span className={checks[svc.key] ? 'text-green-400' : 'text-slate-600'}>{svc.name}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <AnimatePresence>
          {ready && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-xs text-green-400 tracking-widest uppercase"
            >
              System Online
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
