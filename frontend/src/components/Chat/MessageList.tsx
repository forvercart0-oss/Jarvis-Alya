import { useEffect, useRef } from 'react'
import type { Message, ToolCall } from '../../types'
import { MessageBubble } from './MessageBubble'
import { ToolCallDisplay } from './ToolCallDisplay'

interface MessageListProps {
  messages: Message[]
  toolCalls: ToolCall[]
  streaming: boolean
  onCopy?: (content: string) => void
  onQuickAction?: (action: string) => void
}

export function MessageList({ messages, toolCalls, streaming, onCopy, onQuickAction }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, toolCalls])

  if (messages.length === 0 && toolCalls.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center gap-4 opacity-60">
        <div className="text-cyan-400/60 text-xs tracking-[0.4em] uppercase">Awaiting Input</div>
        <div className="text-slate-500 text-xs max-w-sm leading-relaxed">
          Try: &quot;What&apos;s my CPU usage?&quot;, &quot;Open Firefox&quot;, &quot;Remember that my favorite editor is Neovim&quot;, &quot;What time is it?&quot;
        </div>
        {onQuickAction && (
          <div className="flex flex-wrap justify-center gap-2 mt-2">
            {[
              { label: 'Check System', action: 'What is my system status?' },
              { label: 'Check Battery', action: 'What is my battery status?' },
              { label: 'What time is it', action: 'What time is it?' },
              { label: 'Open Browser', action: 'Open Firefox' },
            ].map((q) => (
              <button
                key={q.label}
                onClick={() => onQuickAction(q.action)}
                className="px-3 py-1.5 text-[10px] tracking-wider uppercase text-cyan-400/70 border border-cyan-500/20 rounded hover:border-cyan-400/40 hover:text-cyan-300 transition-all"
              >
                {q.label}
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3 chat-scroll">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} onCopy={onCopy} />
      ))}
      {toolCalls.map((t) => (
        <ToolCallDisplay key={t.id} toolCall={t} />
      ))}
      {streaming && (
        <div className="flex justify-start">
          <div className="bg-slate-800/60 px-3 py-2 rounded-lg text-slate-400 text-sm">
            Thinking<span className="cursor-blink" />
          </div>
        </div>
      )}
    </div>
  )
}
