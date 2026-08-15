import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { ToolCall } from '../../types'
import { CheckCircle2, XCircle, Loader2, Activity } from 'lucide-react'

interface ActivityFeedProps {
  toolCalls: ToolCall[]
  notifications: { id: string; message: string; type: 'info' | 'warning' | 'error' }[]
}

export function ActivityFeed({ toolCalls, notifications }: ActivityFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [toolCalls, notifications])

  const recentTools = toolCalls.slice(0, 10)

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto p-4 space-y-2">
      {recentTools.length === 0 && notifications.length === 0 ? (
        <div className="text-center text-slate-600 py-8 text-xs">
          <Activity className="w-6 h-6 mx-auto mb-2 opacity-30" />
          No recent activity
        </div>
      ) : (
        <AnimatePresence>
          {recentTools.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className="glass-panel p-2 flex items-center gap-2"
            >
              {t.status === 'running' && <Loader2 className="w-3 h-3 animate-spin text-cyan-400 flex-shrink-0" />}
              {t.status === 'success' && <CheckCircle2 className="w-3 h-3 text-green-400 flex-shrink-0" />}
              {t.status === 'error' && <XCircle className="w-3 h-3 text-red-400 flex-shrink-0" />}
              <span className="text-xs text-slate-300 truncate">{t.name}</span>
            </motion.div>
          ))}
          {notifications.map((n) => (
            <motion.div
              key={n.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className={`glass-panel p-2 flex items-center gap-2 ${
                n.type === 'error' ? 'border-red-400/30' : n.type === 'warning' ? 'border-yellow-400/30' : ''
              }`}
            >
              <span className="text-xs text-slate-300">{n.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      )}
    </div>
  )
}
