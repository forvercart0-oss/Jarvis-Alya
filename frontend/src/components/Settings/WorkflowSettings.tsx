import type { JarvisSettings } from '../../types'

interface WorkflowSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function WorkflowSettings({ settings, onUpdate }: WorkflowSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xs font-semibold tracking-[0.15em] text-cyan-400/70 uppercase mb-3">Workflow Engine</h3>
        <div className="space-y-3">
          <ToggleRow
            label="Enable Workflow Engine"
            value={!!settings.workflow_max_concurrent}
            onToggle={(v) => onUpdate({ workflow_max_concurrent: v ? 3 : 0 })}
          />
          <NumberRow label="Max Concurrent Workflows" value={settings.workflow_max_concurrent ?? 3} onChange={(v) => onUpdate({ workflow_max_concurrent: v })} min={1} max={10} />
          <NumberRow label="Default Timeout (seconds)" value={settings.workflow_default_timeout ?? 600} onChange={(v) => onUpdate({ workflow_default_timeout: v })} min={60} max={3600} />
          <NumberRow label="Default Retries" value={settings.workflow_default_retries ?? 2} onChange={(v) => onUpdate({ workflow_default_retries: v })} min={0} max={5} />
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold tracking-[0.15em] text-cyan-400/70 uppercase mb-3">Quiet Hours</h3>
        <div className="space-y-3">
          <TextRow label="Quiet Hours Start" value={settings.workflow_quiet_hours_start ?? '23:00'} onChange={(v) => onUpdate({ workflow_quiet_hours_start: v })} placeholder="23:00" />
          <TextRow label="Quiet Hours End" value={settings.workflow_quiet_hours_end ?? '08:00'} onChange={(v) => onUpdate({ workflow_quiet_hours_end: v })} placeholder="08:00" />
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold tracking-[0.15em] text-cyan-400/70 uppercase mb-3">History & Retention</h3>
        <div className="space-y-3">
          <NumberRow label="History Retention (days)" value={settings.workflow_history_retention_days ?? 30} onChange={(v) => onUpdate({ workflow_history_retention_days: v })} min={1} max={365} />
        </div>
      </div>
    </div>
  )
}

function ToggleRow({ label, value, onToggle }: { label: string; value: boolean; onToggle: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-slate-300">{label}</span>
      <button
        onClick={() => onToggle(!value)}
        className={`w-10 h-5 rounded-full transition-all ${value ? 'bg-cyan-500/30' : 'bg-slate-700/50'}`}
      >
        <div className={`w-4 h-4 rounded-full transition-all ${value ? 'translate-x-5 bg-cyan-400' : 'translate-x-0.5 bg-slate-400'}`} />
      </button>
    </div>
  )
}

function NumberRow({ label, value, onChange, min, max }: { label: string; value: number; onChange: (v: number) => void; min: number; max: number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-slate-300">{label}</span>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={(e) => onChange(parseInt(e.target.value, 10) || min)}
        className="w-20 bg-slate-900/50 border border-slate-700/50 rounded px-2 py-1 text-xs text-right focus:outline-none focus:border-cyan-500/50"
      />
    </div>
  )
}

function TextRow({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-slate-300">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-24 bg-slate-900/50 border border-slate-700/50 rounded px-2 py-1 text-xs text-right focus:outline-none focus:border-cyan-500/50"
      />
    </div>
  )
}
