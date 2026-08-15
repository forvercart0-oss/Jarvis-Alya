import type { ToolCall } from '../../types'
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'

interface ToolCallDisplayProps {
  toolCall: ToolCall
}

export function ToolCallDisplay({ toolCall }: ToolCallDisplayProps) {
  const statusIcon =
    toolCall.status === 'running' ? (
      <Loader2 className="w-3 h-3 animate-spin text-cyan-400" />
    ) : toolCall.status === 'success' ? (
      <CheckCircle2 className="w-3 h-3 text-green-400" />
    ) : (
      <XCircle className="w-3 h-3 text-red-400" />
    )

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] px-3 py-2 rounded-lg border border-slate-600/30 bg-slate-800/40">
        <div className="flex items-center gap-2 mb-1">
          {statusIcon}
          <span className="text-xs text-cyan-400 font-mono">{toolCall.name}</span>
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">
            {toolCall.status}
          </span>
        </div>
        {toolCall.arguments && Object.keys(toolCall.arguments).length > 0 && (
          <div className="text-[10px] text-slate-400 font-mono bg-slate-900/50 px-2 py-1 rounded">
            {JSON.stringify(toolCall.arguments)}
          </div>
        )}
        {toolCall.result !== undefined && (
          <div className="mt-1 text-[10px] text-slate-400 font-mono bg-slate-900/50 px-2 py-1 rounded max-h-32 overflow-auto">
            {typeof toolCall.result === 'string'
              ? toolCall.result
              : JSON.stringify(toolCall.result, null, 2)}
          </div>
        )}
      </div>
    </div>
  )
}
