import { useState } from 'react'
import type { OrbState, Message, ToolCall } from '../../types'
import { Trash2, Shield } from 'lucide-react'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'

interface ChatPanelProps {
  messages: Message[]
  toolCalls: ToolCall[]
  orbState: OrbState
  streaming: boolean
  onSend: (text: string) => void
  onVoice: () => void
  onStop: () => void
  onClear: () => void
  onCopy: (content: string) => void
  micAvailable: boolean
  pendingToolConfirmation?: { tool: string; arguments: Record<string, any>; message: string; tool_call_id: string } | null
  onConfirmTool?: (confirmed: boolean) => void
  onQuickAction?: (action: string) => void
}

export function ChatPanel({
  messages,
  toolCalls,
  orbState,
  streaming,
  onSend,
  onVoice,
  onStop,
  onClear,
  onCopy,
  micAvailable,
  pendingToolConfirmation,
  onConfirmTool,
  onQuickAction,
}: ChatPanelProps) {
  const [dragOver, setDragOver] = useState(false)
  const [attachedFile, setAttachedFile] = useState<File | null>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0]
      if (file.type.startsWith('image/')) {
        setAttachedFile(file)
      }
    }
  }

  const handleImageSelect = (file: File) => {
    setAttachedFile(file)
  }

  const handleImageRemove = () => {
    setAttachedFile(null)
  }

  return (
    <div
      className="flex flex-col h-full min-h-0"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {dragOver && (
        <div className="absolute inset-0 bg-cyan-500/10 border-2 border-cyan-400/40 rounded-lg flex items-center justify-center z-50 pointer-events-none">
          <span className="text-cyan-300 text-sm tracking-wider">DROP IMAGE</span>
        </div>
      )}
      <div className="flex items-center justify-between px-4 py-2 border-b border-cyan-500/10">
        <span className="text-[11px] tracking-[0.3em] text-cyan-400/70 uppercase">
          Communication Channel
        </span>
        <div className="flex gap-2">
          <button
            onClick={onClear}
            className="text-[10px] tracking-widest text-slate-500 hover:text-cyan-300 transition-colors uppercase flex items-center gap-1"
            title="Clear conversation"
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
          <span className="text-[10px] text-slate-600">{messages.length} msgs</span>
        </div>
      </div>

      <MessageList
        messages={messages}
        toolCalls={toolCalls}
        streaming={streaming}
        onCopy={onCopy}
        onQuickAction={onQuickAction || onSend}
      />

      <MessageInput
        onSend={onSend}
        onVoice={onVoice}
        onStop={onStop}
        orbState={orbState}
        streaming={streaming}
        micAvailable={micAvailable}
        onImageSelect={handleImageSelect}
        onImageRemove={handleImageRemove}
        attachedImage={attachedFile ? { name: attachedFile.name, size: attachedFile.size, url: URL.createObjectURL(attachedFile) } : null}
      />

      {pendingToolConfirmation && (
        <div className="px-4 py-3 border-t border-yellow-500/30 bg-yellow-500/5">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-4 h-4 text-yellow-400" />
            <span className="text-xs text-yellow-400 font-medium">Confirmation Required</span>
          </div>
          <p className="text-xs text-slate-300 mb-3">{pendingToolConfirmation.message}</p>
          <div className="flex gap-2">
            <button
              onClick={() => onConfirmTool?.(true)}
              className="px-3 py-1.5 bg-yellow-500/15 border border-yellow-400/40 rounded text-xs text-yellow-200 hover:bg-yellow-400/25 transition-all"
            >
              Confirm
            </button>
            <button
              onClick={() => onConfirmTool?.(false)}
              className="px-3 py-1.5 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-400 hover:bg-slate-700 transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
