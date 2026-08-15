import type { JarvisSettings } from '../../types'
import { Button } from '../Common'

interface SecuritySettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function SecuritySettings({ settings, onUpdate }: SecuritySettingsProps) {
  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Security</h3>
      <div>
        <label className="block text-xs text-slate-400 mb-1">GROQ API Key</label>
        <input
          type="password"
          value={settings.groq_api_key || ''}
          onChange={(e) => onUpdate({ groq_api_key: e.target.value })}
          placeholder="gsk_..."
          className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 font-mono"
        />
        <p className="text-[10px] text-slate-500 mt-1">Stored securely on the backend. Never exposed to the browser.</p>
      </div>
      <Button variant="secondary" onClick={async () => {
        try {
          const res = await fetch('/api/health')
          const data = await res.json()
          alert(`Groq: ${data.groq.status}\n${data.groq.error || 'Connected'}`)
        } catch {
          alert('Failed to test connection')
        }
      }}>Test Groq Connection</Button>
    </div>
  )
}
