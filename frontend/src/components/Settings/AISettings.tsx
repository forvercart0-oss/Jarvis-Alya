import type { JarvisSettings } from '../../types'
import { Input, Toggle, Button } from '../Common'

interface AISettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function AISettings({ settings, onUpdate }: AISettingsProps) {
  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">AI Models</h3>
      <div>
        <label className="block text-xs text-slate-400 mb-1">AI Provider</label>
        <select
          value={settings.provider_priority?.startsWith('local') ? 'local' : 'groq'}
          onChange={(e) => onUpdate({ provider_priority: e.target.value === 'local' ? 'local_first' : 'groq_first' })}
          className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
        >
          <option value="groq">Groq Cloud</option>
          <option value="local">Local LLM</option>
        </select>
      </div>
      <Input label="GROQ Model" value={settings.groq_model} onChange={(v: string) => onUpdate({ groq_model: v })} placeholder="llama-3.3-70b-versatile" />
      <Toggle label="Auto Failover" checked={settings.auto_failover} onChange={(v: boolean) => onUpdate({ auto_failover: v })} description="Automatically fall back to secondary provider on failure" />
      <Button variant="secondary" onClick={async () => {
        try {
          const res = await fetch('/api/health')
          const data = await res.json()
          alert(`Groq: ${data.groq.status}\n${data.groq.error || 'OK'}`)
        } catch {
          alert('Failed to check health')
        }
      }}>Test Groq Connection</Button>
    </div>
  )
}
