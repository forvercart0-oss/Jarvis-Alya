import type { OrbState } from '../../types'
import { Mic, MicOff } from 'lucide-react'
import { motion } from 'framer-motion'

interface MicButtonProps {
  state: OrbState
  onClick: () => void
  available: boolean
}

export function MicButton({ state, onClick, available }: MicButtonProps) {
  const isListening = state === 'listening'

  return (
    <motion.button
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      disabled={!available}
      className={`relative p-3 rounded-full transition-all ${
        isListening
          ? 'bg-cyan-500/20 border-2 border-cyan-400 shadow-[0_0_20px_rgba(0,240,255,0.4)]'
          : 'bg-slate-800/80 border border-cyan-500/30 hover:border-cyan-400/60'
      } ${!available ? 'opacity-30 cursor-not-allowed' : ''}`}
      title={isListening ? 'Stop listening' : 'Start voice input'}
    >
      {isListening ? (
        <MicOff className="w-5 h-5 text-cyan-400" />
      ) : (
        <Mic className="w-5 h-5 text-cyan-400" />
      )}
      {isListening && (
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-cyan-400/50"
          animate={{ scale: [1, 1.3], opacity: [0.5, 0] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
        />
      )}
    </motion.button>
  )
}
