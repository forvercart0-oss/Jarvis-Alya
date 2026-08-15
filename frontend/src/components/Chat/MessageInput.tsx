import { useState, useRef, useEffect } from 'react'
import type { OrbState } from '../../types'
import { Mic, MicOff, Send, Square } from 'lucide-react'

interface MessageInputProps {
  onSend: (text: string) => void
  onVoice: () => void
  onStop: () => void
  orbState: OrbState
  streaming: boolean
  micAvailable: boolean
  disabled?: boolean
}

export function MessageInput({
  onSend,
  onVoice,
  onStop,
  orbState,
  streaming,
  micAvailable,
  disabled = false,
}: MessageInputProps) {
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (orbState === 'idle' || orbState === 'listening') {
      inputRef.current?.focus()
    }
  }, [orbState])

  const submit = () => {
    const text = input.trim()
    if (!text) return
    onSend(text)
    setInput('')
  }

  return (
    <div className="px-4 py-3 border-t border-cyan-500/10 flex items-center gap-2">
      <input
        ref={inputRef}
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            submit()
          }
          if (e.key === 'Escape') {
            if (streaming) onStop()
            setInput('')
          }
        }}
        placeholder='Speak or type a command...'
        disabled={disabled || streaming}
        className="flex-1 bg-slate-900/80 border border-cyan-500/20 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 focus:shadow-[0_0_12px_rgba(0,240,255,0.15)] transition-all disabled:opacity-50"
      />

      <button
        onClick={onVoice}
        disabled={!micAvailable || disabled || streaming}
        className="p-2 rounded-lg bg-slate-800 border border-cyan-500/20 text-cyan-300 hover:bg-cyan-500/10 hover:shadow-[0_0_12px_rgba(0,240,255,0.25)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
        title={micAvailable ? 'Voice input' : 'Microphone unavailable'}
      >
        {orbState === 'listening' ? <MicOff className="w-5 h-5 animate-pulse" /> : <Mic className="w-5 h-5" />}
      </button>

      {streaming ? (
        <button
          onClick={onStop}
          className="p-2 rounded-lg bg-red-500/20 border border-red-500/40 text-red-300 hover:bg-red-500/30 transition-all"
          title="Stop generation"
        >
          <Square className="w-5 h-5" />
        </button>
      ) : (
        <button
          onClick={submit}
          disabled={!input.trim() || disabled}
          className="px-4 py-2 rounded-lg bg-cyan-500/15 border border-cyan-400/40 text-cyan-200 text-sm hover:bg-cyan-400/25 hover:shadow-[0_0_14px_rgba(0,240,255,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-5 h-5" />
        </button>
      )}
    </div>
  )
}
