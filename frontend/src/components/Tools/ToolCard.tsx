import { useState } from 'react'
import type { ToolInfo } from '../../types'
import { Wrench, AlertTriangle, Play } from 'lucide-react'

interface ToolCardProps {
  tool: ToolInfo
  onExecute: (name: string, args: Record<string, any>) => void
}

export function ToolCard({ tool, onExecute }: ToolCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="glass-panel p-3 cursor-pointer hover:border-cyan-400/40 transition-colors">
      <div className="flex items-start justify-between gap-2" onClick={() => setExpanded(!expanded)}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Wrench className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span className="text-sm text-cyan-400 font-mono truncate">{tool.name}</span>
            {tool.requires_confirmation && (
              <span className="text-yellow-400" title="Requires confirmation">
                <AlertTriangle className="w-3 h-3" />
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">{tool.description}</p>
        </div>
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-cyan-500/10">
          <QuickActionForm toolName={tool.name} onExecute={onExecute} requiresConfirmation={tool.requires_confirmation} />
        </div>
      )}
    </div>
  )
}

interface QuickActionFormProps {
  toolName: string
  onExecute: (name: string, args: Record<string, any>) => void
  requiresConfirmation: boolean
}

function QuickActionForm({ toolName, onExecute, requiresConfirmation }: QuickActionFormProps) {
  const [args, setArgs] = useState('')
  const [confirming, setConfirming] = useState(false)

  const handleExecute = () => {
    let parsed: Record<string, any> = {}
    try {
      parsed = JSON.parse(args || '{}')
    } catch {
      alert('Invalid JSON arguments')
      return
    }
    if (requiresConfirmation && !confirming) {
      setConfirming(true)
      return
    }
    onExecute(toolName, parsed)
    setConfirming(false)
    setArgs('')
  }

  return (
    <div className="space-y-2">
      <input
        type="text"
        value={args}
        onChange={(e) => setArgs(e.target.value)}
        placeholder='JSON arguments (optional)'
        className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 font-mono"
      />
      <button
        onClick={handleExecute}
        className="flex items-center gap-1 px-3 py-1.5 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all"
      >
        <Play className="w-3 h-3" />
        {requiresConfirmation && confirming ? 'Confirm Execute' : 'Execute'}
      </button>
    </div>
  )
}
