import { useState } from 'react'
import type { Message } from '../../types'
import { motion } from 'framer-motion'

interface MessageBubbleProps {
  message: Message
  onCopy?: (content: string) => void
}

export function MessageBubble({ message, onCopy }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    if (!onCopy) return
    await onCopy(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  const isSerious = isSystem && message.content.includes('SERIOUS MODE')
  const isResearch = isSystem && message.content.includes('DEEP RESEARCH')

  let bubbleColor = 'bg-slate-800/60 text-slate-200 border border-slate-600/30 rounded-bl-sm'
  if (isUser) bubbleColor = 'bg-cyan-500/10 text-cyan-100 border border-cyan-400/20 rounded-br-sm'
  if (isSerious) bubbleColor = 'bg-red-500/10 text-red-200 border border-red-500/30 rounded-sm'
  if (isResearch) bubbleColor = 'bg-red-500/10 text-red-200 border border-red-500/30 rounded-sm'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={[
          'max-w-[85%] px-3 py-2 rounded-lg text-sm leading-relaxed break-words relative group',
          bubbleColor,
        ].join(' ')}
      >
        {!isUser && !isSystem && (
          <div className="text-[9px] tracking-[0.3em] text-cyan-400/50 uppercase mb-1">JARVIS</div>
        )}
        {isSerious && (
          <div className="text-[9px] tracking-[0.3em] text-red-400/70 uppercase mb-1 font-bold">SERIOUS MODE</div>
        )}
        {isResearch && !isSerious && (
          <div className="text-[9px] tracking-[0.3em] text-red-400/70 uppercase mb-1 font-bold">DEEP RESEARCH</div>
        )}
        <div className="whitespace-pre-wrap">{message.content}</div>
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.toolCalls.map((tc) => (
              <div key={tc.id} className="text-[10px] text-slate-400 border-t border-slate-700/50 pt-1">
                <span className="text-cyan-400">{tc.name}</span>
                <span className="text-slate-500 ml-1">
                  {tc.status === 'running' ? 'running...' : tc.status === 'success' ? 'done' : 'failed'}
                </span>
              </div>
            ))}
          </div>
        )}
        {!isUser && !isSystem && (
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-slate-500 hover:text-cyan-400 text-xs"
            title="Copy"
          >
            {copied ? 'Copied' : 'Copy'}
          </button>
        )}
      </div>
    </motion.div>
  )
}
