import type { JarvisSettings } from '../../types'
import { Input, Toggle, Button } from '../Common'

interface LocalAISettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function LocalAISettings({ settings, onUpdate }: LocalAISettingsProps) {
  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Local AI</h3>
      <Toggle label="Enable Local LLM" checked={settings.local_llm_enabled} onChange={(v: boolean) => onUpdate({ local_llm_enabled: v })} />
      {settings.local_llm_enabled && (
        <>
          <Input label="Local LLM URL" value={settings.local_llm_url} onChange={(v: string) => onUpdate({ local_llm_url: v })} placeholder="http://localhost:11434" />
          <Input label="Local LLM Model" value={settings.local_llm_model} onChange={(v: string) => onUpdate({ local_llm_model: v })} placeholder="llama3" />
          <div>
            <label className="block text-xs text-slate-400 mb-1">API Type</label>
            <select
              value={settings.local_llm_api_type}
              onChange={(e) => onUpdate({ local_llm_api_type: e.target.value })}
              className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
            >
              <option value="openai">OpenAI Compatible</option>
              <option value="ollama">Ollama</option>
              <option value="custom">Custom HTTP</option>
            </select>
          </div>
          <Input label="Timeout (seconds)" type="number" value={String(settings.local_llm_timeout)} onChange={(v: string) => onUpdate({ local_llm_timeout: parseInt(v) || 60 })} />
          <Button variant="secondary" onClick={async () => {
            try {
              const res = await fetch('/api/health')
              const data = await res.json()
              alert(`Local LLM: ${data.local_llm.status}\n${data.local_llm.error || 'OK'}`)
            } catch {
              alert('Failed to check health')
            }
          }}>Test Connection</Button>
        </>
      )}
    </div>
  )
}
