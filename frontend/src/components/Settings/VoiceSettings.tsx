import { useEffect, useState } from 'react'
import type { JarvisSettings } from '../../types'
import { Input, Toggle, Button, Slider } from '../Common'
import { api } from '../../services/api'
import { Volume2, Play, Mic } from 'lucide-react'

interface VoiceSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

interface VoiceStatus {
  initialized: boolean
  mic_available: boolean
  tts_available: boolean
  tts_backend: string | null
  tts_engine: string
  speaking: boolean
}

const inputCls =
  'w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 focus:shadow-[0_0_12px_rgba(0,240,255,0.15)] transition-all'

export function VoiceSettings({ settings, onUpdate }: VoiceSettingsProps) {
  const [status, setStatus] = useState<VoiceStatus | null>(null)
  const [voices, setVoices] = useState<string[]>([])
  const [testText, setTestText] = useState('Hello! This is JARVIS speaking.')
  const [testing, setTesting] = useState(false)

  const refreshStatus = async () => {
    try {
      const [s, v] = await Promise.all([api.getVoiceStatus(), api.getVoiceVoices().catch(() => null)])
      setStatus(s)
      if (v) setVoices(v.voices)
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    refreshStatus()
    const timer = setInterval(refreshStatus, 5000)
    return () => clearInterval(timer)
  }, [])

  const handleTest = async () => {
    setTesting(true)
    try {
      await api.testVoice(testText)
    } catch {
      // ignore
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Voice</h3>

      <div className="glass-panel p-3 space-y-1.5">
        <div className="flex items-center gap-2 text-xs">
          <Mic className="w-4 h-4 text-slate-500" />
          <span className="text-slate-400">Microphone:</span>
          <span className={status?.mic_available ? 'text-green-400' : 'text-red-400'}>
            {status?.mic_available ? 'available' : 'unavailable'}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <Volume2 className="w-4 h-4 text-slate-500" />
          <span className="text-slate-400">TTS:</span>
          <span className={status?.tts_available ? 'text-green-400' : 'text-red-400'}>
            {status?.tts_available ? `${status.tts_engine} (${status.tts_backend || 'unknown'})` : 'unavailable'}
          </span>
          {status?.speaking && <span className="text-cyan-400 animate-pulse">speaking...</span>}
        </div>
      </div>

      <Toggle label="Voice Enabled" checked={settings.voice_enabled} onChange={(v: boolean) => onUpdate({ voice_enabled: v })} />
      <Toggle label="TTS Enabled" checked={settings.tts_enabled} onChange={(v: boolean) => onUpdate({ tts_enabled: v })} />
      <Toggle label="Wake Word" checked={settings.wake_word_enabled} onChange={(v: boolean) => onUpdate({ wake_word_enabled: v })} />
      {settings.wake_word_enabled && (
        <Input label="Wake Word" value={settings.wake_word} onChange={(v: string) => onUpdate({ wake_word: v })} placeholder="Hey JARVIS" />
      )}
      <Input label="Voice Language" value={settings.voice_language} onChange={(v: string) => onUpdate({ voice_language: v })} placeholder="en-US" />

      <div className="space-y-1">
        <label className="text-xs text-slate-400">TTS Engine</label>
        <select value={settings.tts_engine} onChange={(e) => onUpdate({ tts_engine: e.target.value })} className={inputCls}>
          <option value="espeak-ng">espeak-ng (fast, offline)</option>
          <option value="kokoro">kokoro (neural, if installed)</option>
        </select>
      </div>

      <div className="space-y-1">
        <label className="text-xs text-slate-400">TTS Voice</label>
        <select
          value={settings.tts_voice}
          onChange={(e) => onUpdate({ tts_voice: e.target.value })}
          className={inputCls}
        >
          {voices.includes(settings.tts_voice) ? (
            <option value={settings.tts_voice}>{settings.tts_voice}</option>
          ) : (
            <option value={settings.tts_voice}>Custom: {settings.tts_voice}</option>
          )}
          {voices
            .filter((v) => v !== settings.tts_voice)
            .map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
        </select>
      </div>

      <Slider
        label="TTS Speed"
        min={50}
        max={500}
        step={5}
        value={settings.tts_speed}
        onChange={(v: number) => onUpdate({ tts_speed: v })}
      />
      <Slider
        label="TTS Volume"
        min={0}
        max={100}
        step={5}
        value={settings.tts_volume}
        onChange={(v: number) => onUpdate({ tts_volume: v })}
      />

      <div className="space-y-1">
        <label className="text-xs text-slate-400">Test phrase</label>
        <input value={testText} onChange={(e) => setTestText(e.target.value)} className={inputCls} />
        <Button onClick={handleTest} disabled={testing} className="w-full">
          <Play className="w-3 h-3" /> {testing ? 'Speaking...' : 'Test Voice'}
        </Button>
      </div>
    </div>
  )
}
