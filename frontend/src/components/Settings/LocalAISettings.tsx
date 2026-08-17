import { useState, useCallback } from 'react'
import type { JarvisSettings } from '../../types'
import { Input, Toggle } from '../Common'
import { Eye, EyeOff, CheckCircle2, XCircle, Loader2, AlertTriangle } from 'lucide-react'

interface LocalAISettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

const inputCls = 'w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 focus:shadow-[0_0_12px_rgba(0,240,255,0.15)] transition-all font-mono'

export function LocalAISettings({ settings, onUpdate }: LocalAISettingsProps) {
  const [showKey, setShowKey] = useState(false)
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle')
  const [testError, setTestError] = useState('')

  const handleTest = useCallback(async () => {
    setTestStatus('testing')
    setTestError('')
    try {
      const res = await fetch('/api/health')
      const data = await res.json()
      const localStatus = data.providers?.local_llm
      if (localStatus?.status === 'online') {
        setTestStatus('success')
      } else {
        setTestStatus('error')
        setTestError(localStatus?.error || 'Local LLM not reachable. Make sure Ollama or your local server is running.')
      }
    } catch {
      setTestStatus('error')
      setTestError('Failed to reach backend server')
    }
  }, [])

  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Local AI</h3>

      <Toggle
        label="Enable Local LLM"
        checked={settings.local_llm_enabled}
        onChange={(v: boolean) => onUpdate({ local_llm_enabled: v })}
      />

      {settings.local_llm_enabled && (
        <>
          <Input
            label="Local LLM URL"
            value={settings.local_llm_url}
            onChange={(v: string) => onUpdate({ local_llm_url: v })}
            placeholder="http://localhost:11434"
          />

          <div>
            <label className="block text-xs text-slate-400 mb-1">API Type</label>
            <select
              value={settings.local_llm_api_type}
              onChange={(e) => onUpdate({ local_llm_api_type: e.target.value })}
              className={inputCls}
            >
              <option value="openai">OpenAI Compatible</option>
              <option value="ollama">Ollama</option>
              <option value="custom">Custom HTTP</option>
            </select>
          </div>

          <Input
            label="Model"
            value={settings.local_llm_model}
            onChange={(v: string) => onUpdate({ local_llm_model: v })}
            placeholder="llama3, mistral, codellama, etc."
          />

          <div>
            <label className="block text-xs text-slate-400 mb-1">API Key (optional)</label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={settings.local_llm_api_key || ''}
                onChange={(e) => onUpdate({ local_llm_api_key: e.target.value })}
                placeholder="Leave empty if no key required"
                className={inputCls + ' pr-8'}
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              >
                {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          <Input
            label="Timeout (seconds)"
            type="number"
            value={String(settings.local_llm_timeout)}
            onChange={(v: string) => onUpdate({ local_llm_timeout: parseInt(v) || 60 })}
          />

          <div className="flex items-center gap-3">
            <button
              onClick={handleTest}
              disabled={testStatus === 'testing'}
              className="px-4 py-2 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-300 hover:bg-slate-700 transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              {testStatus === 'testing' ? (
                <><Loader2 className="w-3 h-3 animate-spin" /> Testing...</>
              ) : (
                <>Test Connection</>
              )}
            </button>
            {testStatus === 'success' && (
              <span className="flex items-center gap-1 text-xs text-green-400">
                <CheckCircle2 className="w-3 h-3" /> Connected
              </span>
            )}
            {testStatus === 'error' && (
              <span className="flex items-center gap-1 text-xs text-red-400">
                <XCircle className="w-3 h-3" /> Failed
              </span>
            )}
          </div>

          {testError && (
            <div className="flex items-start gap-1.5 text-xs text-red-400/80 bg-red-500/5 rounded p-2">
              <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
              <span>{testError}</span>
            </div>
          )}
        </>
      )}
    </div>
  )
}
