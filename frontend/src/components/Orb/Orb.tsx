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
  vision: 'VISION',
  scanning: 'SCANNING',
  analyzing: 'ANALYZING',
  locating: 'LOCATING',
  acting: 'ACTING',
  screen_mode: 'SCREEN MODE',
  browsing: 'BROWSING',
  navigating: 'NAVIGATING',
  reading: 'READING',
  searching: 'SEARCHING',
  clicking: 'CLICKING',
  typing: 'TYPING',
  verifying: 'VERIFYING',
  downloading: 'DOWNLOADING',
  reading_message: 'READING MESSAGE',
  composing: 'COMPOSING',
  sending: 'SENDING',
  calling: 'CALLING',
  answering: 'ANSWERING',
  ending_call: 'ENDING CALL',
  message_received: 'MESSAGE RECEIVED',
  planning: 'PLANNING',
  editing: 'EDITING',
  running: 'RUNNING',
  testing: 'TESTING',
  debugging: 'DEBUGGING',
  building: 'BUILDING',
  committing: 'COMMITTING',
  deploying: 'DEPLOYING',
  monitoring: 'MONITORING',
  recovering: 'RECOVERING',
}

const STATE_TO_ORB: Record<string, 'working' | 'searching' | 'solving' | 'listening' | 'connecting' | 'weaving' | 'composing' | 'breathing' | 'shaping'> = {
  idle: 'working',
  listening: 'listening',
  thinking: 'breathing',
  processing: 'solving',
  speaking: 'composing',
  error: 'searching',
  vision: 'working',
  scanning: 'searching',
  analyzing: 'breathing',
  locating: 'searching',
  acting: 'solving',
  screen_mode: 'working',
  browsing: 'working',
  navigating: 'connecting',
  reading: 'breathing',
  searching: 'searching',
  clicking: 'solving',
  typing: 'solving',
  verifying: 'breathing',
  downloading: 'composing',
  reading_message: 'breathing',
  composing: 'composing',
  sending: 'connecting',
  calling: 'connecting',
  answering: 'connecting',
  ending_call: 'working',
  message_received: 'composing',
  planning: 'breathing',
  editing: 'solving',
  running: 'working',
  testing: 'breathing',
  debugging: 'solving',
  building: 'working',
  committing: 'connecting',
  deploying: 'working',
  monitoring: 'breathing',
  recovering: 'solving',
}

export function Orb({ state, accentColor = '#00f0ff', size = 64, onStatusChange, onClick }: OrbProps) {
  const [pulse, setPulse] = useState(false)

  const renderSize: 20 | 64 = size <= 42 ? 20 : 64
  const scale = size / renderSize

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
    <div className="relative flex flex-col items-center select-none" style={{ perspective: '800px' }}>
      <div className="relative cursor-pointer" onClick={handleClick} style={{ transformStyle: 'preserve-3d' }}>
        <div
          className="absolute inset-0 rounded-full opacity-40 blur-2xl transition-all duration-700"
          style={{
            background: `radial-gradient(circle, ${glowColor} 0%, transparent 70%)`,
            transform: `translateZ(${(pulse ? 1 : 0) * 5}px)`,
          }}
        />
        <motion.div
          animate={{ scale: pulse ? [1, 1.05, 1] : 1 }}
          transition={{ repeat: pulse ? Infinity : 0, duration: 2 }}
          className="relative"
        >
          <div style={{ width: size, height: size }}>
            <div style={{ transform: `scale(${scale})`, transformOrigin: 'top left', width: renderSize, height: renderSize }}>
              <ThinkingOrb
                state={STATE_TO_ORB[state] || 'working'}
                size={renderSize}
                theme="dark"
                speed={1.2}
                style={{ color: glowColor }}
              />
            </div>
          </div>
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
