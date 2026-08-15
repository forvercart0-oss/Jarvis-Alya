import { motion } from 'framer-motion'
import { RefreshCw, AlertTriangle } from 'lucide-react'

interface OfflineScreenProps {
  error?: string
  onRetry: () => void
}

export function OfflineScreen({ error, onRetry }: OfflineScreenProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-jarvis-dark">
      <div className="text-center space-y-6 max-w-md px-4">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <svg viewBox="0 0 80 80" className="w-20 h-20 text-red-400 mx-auto">
            <path d="M40 10 L70 25 L70 55 L40 70 L10 55 L10 25 Z" fill="none" stroke="currentColor" strokeWidth="2" opacity="0.5" />
            <circle cx="40" cy="40" r="8" fill="currentColor" opacity="0.3" />
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto" />
          </svg>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="space-y-2">
          <h1 className="text-3xl font-bold text-red-400 tracking-[0.3em]">SYSTEM OFFLINE</h1>
          <p className="text-sm text-slate-400">Unable to connect to JARVIS backend</p>
          {error && (
            <div className="glass-panel p-3 text-xs text-red-300 font-mono break-all">
              {error}
            </div>
          )}
        </motion.div>

        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500/15 border border-cyan-400/40 rounded-lg text-cyan-200 text-sm hover:bg-cyan-400/25 hover:shadow-[0_0_14px_rgba(0,240,255,0.3)] transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Retry Connection
        </button>

        <p className="text-[10px] text-slate-600">
          Ensure the backend is running at http://localhost:8000
        </p>
      </div>
    </div>
  )
}
