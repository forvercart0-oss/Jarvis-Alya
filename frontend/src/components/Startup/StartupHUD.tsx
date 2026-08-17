import { motion, AnimatePresence } from 'framer-motion'

export interface HudItem {
  id: string
  label: string
  icon: JSX.Element
  status: 'pending' | 'online' | 'offline' | 'warning'
  detail?: string
}

interface StartupHUDProps {
  items: HudItem[]
  accentColor: string
}

const STATUS_COLORS: Record<HudItem['status'], string> = {
  pending: '#647489',
  online: '#22c55e',
  offline: '#ef4444',
  warning: '#eab308',
}

export function StartupHUD({ items, accentColor }: StartupHUDProps) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 pointer-events-none">
      <AnimatePresence>
        {items.map((item, i) => {
          return (
            <motion.div
              key={item.id}
              className="flex items-center gap-2 text-xs font-mono"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ delay: i * 0.1 }}
              style={{ color: STATUS_COLORS[item.status] }}
            >
              <span
                className="flex items-center justify-center w-4 h-4 rounded-full"
                style={{
                  backgroundColor: `${STATUS_COLORS[item.status]}40`,
                  boxShadow: `0 0 6px ${STATUS_COLORS[item.status]}80`,
                }}
              >
                {item.icon}
              </span>
              <span>{item.label}</span>
              {item.detail && (
                <span className="text-slate-500">
                  {item.detail}
                </span>
              )}
              {item.status === 'online' && (
                <motion.span
                  className="inline-block w-1 h-1 rounded-full"
                  style={{ backgroundColor: STATUS_COLORS.online }}
                  initial={{ scale: 0 }}
                  animate={{ scale: [0, 1.2, 1] }}
                  transition={{ duration: 0.3 }}
                />
              )}
            </motion.div>
          )
        })}
      </AnimatePresence>

      <motion.div
        className="mt-6 text-[10px] uppercase tracking-[0.4em]"
        style={{ color: `${accentColor}80` }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
      >
        JARVIS / ALYA &#8226; INITIALIZATION SEQUENCE
      </motion.div>
    </div>
  )
}
