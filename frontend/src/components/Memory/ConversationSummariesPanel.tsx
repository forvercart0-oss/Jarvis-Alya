import type { ConversationSummaryItem } from '../../types'
import { Clock } from 'lucide-react'

interface ConversationSummariesPanelProps {
  summaries: ConversationSummaryItem[]
}

export function ConversationSummariesPanel({ summaries }: ConversationSummariesPanelProps) {
  return (
    <div className="space-y-3">
      <h4 className="text-xs tracking-widest text-slate-400 uppercase">Conversation Summaries</h4>
      {summaries.length === 0 ? (
        <div className="text-center text-slate-500 py-6">No summaries yet.</div>
      ) : (
        <div className="space-y-2">
          {summaries.map((s) => (
            <div key={s.id} className="glass-panel p-3 space-y-1">
              <div className="text-xs text-slate-300 break-words">{s.summary}</div>
              <div className="flex items-center gap-2 text-[10px] text-slate-600">
                <Clock className="w-3 h-3" />
                <span>{new Date(s.created_at).toLocaleString()}</span>
                <span>• {s.message_count} messages</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
