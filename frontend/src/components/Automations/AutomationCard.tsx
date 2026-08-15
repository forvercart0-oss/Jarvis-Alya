import type { Automation } from '../../types'
import { ToggleLeft, ToggleRight, Play, Trash2, Clock } from 'lucide-react'

interface AutomationCardProps {
  automation: Automation
  onToggle: () => void
  onExecute: () => void
  onDelete: () => void
}

export function AutomationCard({ automation, onToggle, onExecute, onDelete }: AutomationCardProps) {
  return (
    <div className="glass-panel p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-cyan-400 font-mono">{automation.name}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase ${automation.enabled ? 'text-green-400 bg-green-400/10' : 'text-slate-500 bg-slate-700/30'}`}>
              {automation.enabled ? 'Active' : 'Paused'}
            </span>
          </div>
          <div className="text-xs text-slate-400 mt-1">{automation.trigger}</div>
          <div className="text-[10px] text-slate-500 mt-0.5 font-mono truncate">{automation.action}</div>
          {automation.schedule && (
            <div className="flex items-center gap-1 text-[10px] text-slate-500 mt-1">
              <Clock className="w-3 h-3" />
              {automation.schedule}
            </div>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={onExecute}
            className="p-1.5 rounded text-cyan-400 hover:bg-cyan-500/10 transition-colors"
            title="Run now"
          >
            <Play className="w-4 h-4" />
          </button>
          <button
            onClick={onToggle}
            className="p-1.5 rounded text-slate-400 hover:text-cyan-400 transition-colors"
            title={automation.enabled ? 'Disable' : 'Enable'}
          >
            {automation.enabled ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
          </button>
          <button
            onClick={onDelete}
            className="p-1.5 rounded text-red-400 hover:text-red-300 transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
