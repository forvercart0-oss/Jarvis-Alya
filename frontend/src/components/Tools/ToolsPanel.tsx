import type { ToolInfo } from '../../types'
import { ToolCard } from './ToolCard'

interface ToolsPanelProps {
  tools: ToolInfo[]
  onExecute: (name: string, args: Record<string, any>) => void
}

export function ToolsPanel({ tools, onExecute }: ToolsPanelProps) {
  if (tools.length === 0) {
    return (
      <div className="text-center text-slate-500 py-10">No tools available.</div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-3">Available Tools</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {tools.map((tool) => (
          <ToolCard key={tool.name} tool={tool} onExecute={onExecute} />
        ))}
      </div>
    </div>
  )
}
