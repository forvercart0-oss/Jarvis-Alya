import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ThinkingOrb } from 'thinking-orbs'

interface OrbProps {
  state: string
  assistantName: string
  accentColor?: string
  size?: number
  onStatusChange?: (status: string) => void
  onClick?: () => void
}

const STATUS_LABELS: Record<string, string> = {
  idle: 'STANDBY',
  listening: 'LISTENING',
  thinking: 'THINKING',
  processing: 'PROCESSING',
  speaking: 'SPEAKING',
  error: 'ERROR',
}

const STATE_TO_ORB: Record<string, 'working' | 'searching' | 'solving' | 'listening' | 'connecting' | 'weaving' | 'composing' | 'breathing' | 'shaping'> = {
  idle: 'working',
  listening: 'listening',
  thinking: 'breathing',
  processing: 'solving',
  speaking: 'composing',
  error: 'searching',
}

export function Orb({ state, accentColor = '#00f0ff', size = 64, onStatusChange, onClick }: OrbProps) {
  const [pulse, setPulse] = useState(false)

  useEffect(() => {
    if (onStatusChange) onStatusChange(STATUS_LABELS[state] || state.toUpperCase())
    if (state === 'thinking' || state === 'processing' || state === 'speaking') {
      setPulse(true)
    } else {
      setPulse(false)
    }
  }, [state, onStatusChange])

  const glowColor = state === 'error' ? '#ff3333' : accentColor

  const handleClick = () => {
    if (onClick && state !== 'thinking' && state !== 'processing' && state !== 'speaking') {
      onClick()
    }
  }

  return (
    <div className="relative flex flex-col items-center select-none">
      <div className="relative cursor-pointer" onClick={handleClick}>
        <div
          className="absolute inset-0 rounded-full opacity-40 blur-2xl transition-all duration-700"
          style={{
            background: `radial-gradient(circle, ${glowColor} 0%, transparent 70%)`,
            transform: pulse ? 'scale(1.4)' : 'scale(1.1)',
          }}
        />
        <motion.div
          animate={{ scale: pulse ? [1, 1.05, 1] : 1 }}
          transition={{ repeat: pulse ? Infinity : 0, duration: 2 }}
          className="relative"
        >
          <ThinkingOrb
            state={STATE_TO_ORB[state] || 'working'}
            size={size as import('thinking-orbs').OrbSize}
            theme="dark"
            speed={1.2}
            style={{ color: glowColor }}
          />
        </motion.div>
      </div>

      <motion.div
        key={state}
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-5 text-xs tracking-[0.35em] font-light uppercase"
        style={{ color: glowColor }}
      >
        {STATUS_LABELS[state] || state.toUpperCase()}
      </motion.div>

      <div className="mt-1 text-[10px] tracking-widest uppercase opacity-50" style={{ color: glowColor }}>
        {state === 'speaking' ? 'audio output' : state === 'listening' ? 'input armed' : state === 'thinking' || state === 'processing' ? 'neural processing' : 'click to speak'}
      </div>
    </div>
  )
}
