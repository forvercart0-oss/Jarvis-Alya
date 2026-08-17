import { useState, useCallback } from 'react'
import type { JarvisSettings } from '../../types'
import { Input, Toggle } from '../Common'
import { Eye, EyeOff, CheckCircle2, XCircle, Loader2, AlertTriangle, RefreshCw } from 'lucide-react'

interface AISettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

type ProviderId = 'groq' | 'gemini' | 'openrouter' | 'local'

interface ProviderCard {
  id: ProviderId
  name: string
  requiresKey: boolean
  description: string
}

const PROVIDERS: ProviderCard[] = [
  { id: 'groq', name: 'Groq Cloud', requiresKey: true, description: 'Fast inference via Groq API' },
  { id: 'gemini', name: 'Google Gemini', requiresKey: true, description: 'Google AI language models' },
  { id: 'openrouter', name: 'OpenRouter', requiresKey: true, description: 'Multi-model API gateway' },
  { id: 'local', name: 'Local LLM', requiresKey: false, description: 'Ollama / OpenAI-compatible local models' },
]

const GROQ_MODELS = [
  'llama-3.3-70b-versatile',
  'llama-3.1-8b-instant',
  'mixtral-8x7b-32768',
  'gemma2-9b-it',
  'meta-llama/llama-4-scout-17b-16e-instruct',
]

const GEMINI_MODELS = [
  'gemini-2.0-flash',
  'gemini-2.0-flash-lite',
  'gemini-1.5-pro',
  'gemini-1.5-flash',
]

const OPENROUTER_MODELS = [
  'anthropic/claude-sonnet-4',
  'anthropic/claude-3.5-sonnet',
  'openai/gpt-4o',
  'openai/gpt-4o-mini',
  'google/gemini-2.0-flash-001',
  'meta-llama/llama-3.3-70b-instruct',
]

const inputCls = 'w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 focus:shadow-[0_0_12px_rgba(0,240,255,0.15)] transition-all font-mono'

type ConnectionStatus = 'idle' | 'testing' | 'success' | 'error'

export function AISettings({ settings, onUpdate }: AISettingsProps) {
  const [expandedProvider, setExpandedProvider] = useState<ProviderId | null>(() => {
    const pp = settings.provider_priority || 'groq_first'
    if (pp.includes('gemini')) return 'gemini'
    if (pp.includes('openrouter')) return 'openrouter'
    if (pp.includes('local')) return 'local'
    return 'groq'
  })
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [testStatus, setTestStatus] = useState<Record<ProviderId, ConnectionStatus>>({
    groq: 'idle', gemini: 'idle', openrouter: 'idle', local: 'idle',
  })
  const [testErrors, setTestErrors] = useState<Record<ProviderId, string>>({
    groq: '', gemini: '', openrouter: '', local: '',
  })

  const toggleKeyVisibility = useCallback((key: string) => {
    setShowKeys((prev) => ({ ...prev, [key]: !prev[key] }))
  }, [])

  const handleTestConnection = useCallback(async (provider: ProviderId) => {
    setTestStatus((prev) => ({ ...prev, [provider]: 'testing' }))
    setTestErrors((prev) => ({ ...prev, [provider]: '' }))
    try {
      const res = await fetch('/api/health')
      const data = await res.json()
      const providerData = data.providers?.[provider]
      if (providerData?.status === 'online') {
        setTestStatus((prev) => ({ ...prev, [provider]: 'success' }))
      } else {
        setTestStatus((prev) => ({ ...prev, [provider]: 'error' }))
        setTestErrors((prev) => ({ ...prev, [provider]: providerData?.error || 'Provider not configured or unreachable' }))
      }
    } catch {
      setTestStatus((prev) => ({ ...prev, [provider]: 'error' }))
      setTestErrors((prev) => ({ ...prev, [provider]: 'Failed to reach backend' }))
    }
  }, [])

  const getKeyForProvider = useCallback((provider: ProviderId): string => {
    switch (provider) {
      case 'groq': return settings.groq_api_key || ''
      case 'gemini': return settings.gemini_api_key || ''
      case 'openrouter': return settings.openrouter_api_key || ''
      case 'local': return settings.local_llm_api_key || ''
    }
  }, [settings])

  const getModelForProvider = useCallback((provider: ProviderId): string => {
    switch (provider) {
      case 'groq': return settings.groq_model || ''
      case 'gemini': return settings.gemini_model || ''
      case 'openrouter': return settings.openrouter_model || ''
      case 'local': return settings.local_llm_model || ''
    }
  }, [settings])

  const getModelsForProvider = useCallback((provider: ProviderId): string[] => {
    switch (provider) {
      case 'groq': return GROQ_MODELS
      case 'gemini': return GEMINI_MODELS
      case 'openrouter': return OPENROUTER_MODELS
      case 'local': return []
    }
  }, [])

  const handleKeyUpdate = useCallback((provider: ProviderId, key: string) => {
    switch (provider) {
      case 'groq': onUpdate({ groq_api_key: key }); break
      case 'gemini': onUpdate({ gemini_api_key: key }); break
      case 'openrouter': onUpdate({ openrouter_api_key: key }); break
      case 'local': onUpdate({ local_llm_api_key: key }); break
    }
  }, [onUpdate])

  const handleModelUpdate = useCallback((provider: ProviderId, model: string) => {
    switch (provider) {
      case 'groq': onUpdate({ groq_model: model }); break
      case 'gemini': onUpdate({ gemini_model: model }); break
      case 'openrouter': onUpdate({ openrouter_model: model }); break
      case 'local': onUpdate({ local_llm_model: model }); break
    }
  }, [onUpdate])

  const getActiveProvider = useCallback((): ProviderId => {
    const pp = settings.provider_priority || 'groq_first'
    if (pp.includes('gemini')) return 'gemini'
    if (pp.includes('openrouter')) return 'openrouter'
    if (pp.includes('local')) return 'local'
    return 'groq'
  }, [settings.provider_priority])

  const handleSetActiveProvider = useCallback((provider: ProviderId) => {
    onUpdate({ provider_priority: `${provider}_first` })
  }, [onUpdate])

  const renderTestButton = (provider: ProviderId) => {
    const status = testStatus[provider]
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={() => handleTestConnection(provider)}
          disabled={status === 'testing'}
          className="px-3 py-1.5 bg-slate-800 border border-slate-600/30 rounded text-xs text-slate-300 hover:bg-slate-700 transition-all flex items-center gap-1.5 disabled:opacity-50"
        >
          {status === 'testing' ? (
            <><Loader2 className="w-3 h-3 animate-spin" /> Testing...</>
          ) : (
            <>Test Connection</>
          )}
        </button>
        {status === 'success' && (
          <span className="flex items-center gap-1 text-xs text-green-400">
            <CheckCircle2 className="w-3 h-3" /> Connected
          </span>
        )}
        {status === 'error' && (
          <span className="flex items-center gap-1 text-xs text-red-400" title={testErrors[provider]}>
            <XCircle className="w-3 h-3" /> Failed
          </span>
        )}
      </div>
    )
  }

  const renderProviderCard = (card: ProviderCard) => {
    const isActive = getActiveProvider() === card.id
    const isExpanded = expandedProvider === card.id
    const apiKey = getKeyForProvider(card.id)
    const model = getModelForProvider(card.id)
    const models = getModelsForProvider(card.id)
    const hasKey = card.requiresKey ? !!apiKey : true

    return (
      <div
        key={card.id}
        className={`rounded-lg border transition-all ${
          isActive
            ? 'border-cyan-500/40 bg-cyan-500/5'
            : 'border-slate-700/50 bg-slate-800/30 hover:border-slate-600/50'
        }`}
      >
        <button
          onClick={() => setExpandedProvider(isExpanded ? null : card.id)}
          className="w-full flex items-center justify-between p-3 text-left"
        >
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-cyan-400 shadow-[0_0_8px_rgba(0,240,255,0.6)]' : 'bg-slate-600'}`} />
            <div>
              <div className="text-sm text-slate-200 font-medium">{card.name}</div>
              <div className="text-[10px] text-slate-500">{card.description}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {card.requiresKey && (
              <span className={`text-[10px] px-2 py-0.5 rounded ${hasKey ? 'bg-green-500/10 text-green-400' : 'bg-yellow-500/10 text-yellow-400'}`}>
                {hasKey ? 'Key Set' : 'No Key'}
              </span>
            )}
            {!card.requiresKey && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400">
                No Key Required
              </span>
            )}
            {isActive && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400">
                Active
              </span>
            )}
          </div>
        </button>

        {isExpanded && (
          <div className="px-3 pb-3 space-y-3 border-t border-slate-700/30 pt-3">
            {!isActive && (
              <button
                onClick={() => handleSetActiveProvider(card.id)}
                className="px-3 py-1.5 bg-cyan-500/10 border border-cyan-500/30 rounded text-xs text-cyan-400 hover:bg-cyan-500/20 transition-all"
              >
                Set as Active Provider
              </button>
            )}

            {card.requiresKey && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">API Key</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type={showKeys[card.id] ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => handleKeyUpdate(card.id, e.target.value)}
                      placeholder={card.id === 'groq' ? 'gsk_...' : card.id === 'gemini' ? 'AIza...' : 'sk-or-...'}
                      className={inputCls + ' pr-8'}
                    />
                    <button
                      onClick={() => toggleKeyVisibility(card.id)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                    >
                      {showKeys[card.id] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs text-slate-400 mb-1">Model</label>
              {models.length > 0 ? (
                <div className="space-y-1">
                  <select
                    value={model}
                    onChange={(e) => handleModelUpdate(card.id, e.target.value)}
                    className={inputCls}
                  >
                    <option value="">Select model...</option>
                    {models.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={model}
                    onChange={(e) => handleModelUpdate(card.id, e.target.value)}
                    placeholder="Or enter custom model ID"
                    className={inputCls}
                  />
                </div>
              ) : (
                <Input
                  label=""
                  value={model}
                  onChange={(v: string) => handleModelUpdate(card.id, v)}
                  placeholder={card.id === 'local' ? 'llama3, mistral, etc.' : 'model-id'}
                />
              )}
            </div>

            {renderTestButton(card.id)}

            {testErrors[card.id] && (
              <div className="flex items-start gap-1.5 text-xs text-red-400/80 bg-red-500/5 rounded p-2">
                <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                <span>{testErrors[card.id]}</span>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4 max-w-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase">AI Providers</h3>
        <div className="flex items-center gap-2">
          <Toggle
            label="Auto Failover"
            checked={settings.auto_failover}
            onChange={(v: boolean) => onUpdate({ auto_failover: v })}
          />
        </div>
      </div>

      {settings.auto_failover && (
        <div className="flex items-center gap-2 text-[10px] text-slate-500 bg-slate-800/30 rounded p-2 border border-slate-700/30">
          <RefreshCw className="w-3 h-3" />
          <span>When the active provider fails, JARVIS will automatically fall back to the next available provider.</span>
        </div>
      )}

      <div className="space-y-2">
        {PROVIDERS.map(renderProviderCard)}
      </div>

      <div className="pt-2 border-t border-cyan-500/10">
        <div className="text-[10px] text-slate-600 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          API keys are stored locally and never sent to third parties.
        </div>
      </div>
    </div>
  )
}
