import { useEffect, useState } from 'react'
import type { ConversationSummary } from '../../types'
import { History, Trash2, Plus, MessageSquare } from 'lucide-react'
import { api } from '../../services/api'

interface ConversationHistoryProps {
  currentConversationId: string | null
  onSelect: (conversationId: string) => void
  onNew: () => void
  onDelete: (conversationId: string) => void
}

export function ConversationHistory({ currentConversationId, onSelect, onNew, onDelete }: ConversationHistoryProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(false)

  const fetchConversations = async () => {
    setLoading(true)
    try {
      const data = await api.getConversations(50)
      setConversations(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConversations()
    const timer = setInterval(fetchConversations, 8000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 pb-2">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase">Conversations</h3>
        <div className="flex gap-2">
          <button
            onClick={() => {
              onNew()
              setConversations([])
            }}
            className="text-[10px] tracking-widest text-cyan-400 hover:text-cyan-300 transition-colors uppercase flex items-center gap-1"
          >
            <Plus className="w-3 h-3" /> New
          </button>
          <button
            onClick={fetchConversations}
            className="text-[10px] tracking-widest text-slate-500 hover:text-cyan-300 transition-colors uppercase"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
        {loading && conversations.length === 0 && (
          <div className="text-center text-slate-600 text-xs py-8">Loading...</div>
        )}

        {!loading && conversations.length === 0 && (
          <div className="text-center text-slate-500 py-10 text-xs">No conversations yet.</div>
        )}

        {conversations.map((conv) => (
          <div
            key={conv.id}
            onClick={() => onSelect(conv.id)}
            className={`glass-panel p-3 cursor-pointer transition-colors group ${
              conv.id === currentConversationId ? 'border-cyan-400/50' : 'hover:border-cyan-400/40'
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <History className="w-4 h-4 text-slate-500 shrink-0" />
                <span className="text-xs text-slate-300 truncate">{conv.title || conv.preview || 'Untitled'}</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete(conv.id)
                }}
                className="text-slate-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                title="Delete conversation"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
            {conv.preview && (
              <div className="text-[10px] text-slate-500 mt-1 truncate">{conv.preview}</div>
            )}
            <div className="flex items-center gap-2 mt-1.5">
              <span className="text-[10px] text-slate-600 flex items-center gap-1">
                <MessageSquare className="w-3 h-3" /> {conv.message_count} msgs
              </span>
              <span className="text-[10px] text-slate-600">
                {new Date(conv.timestamp).toLocaleString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
