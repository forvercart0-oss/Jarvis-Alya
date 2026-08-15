import { useMemo, useState } from 'react'
import type { JarvisSettings, OrbState, VoiceInfo } from '../../types'
import { Mic, MicOff, Volume2, AudioLines, Gauge, Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'
import { Slider } from '../Common/Slider'

interface VoicePanelProps {
  orbState: OrbState
  onVoice: () => void
  onSpeak: (text: string) => void
  voiceAvailable: boolean
  settings: JarvisSettings | null
  voiceInfo: VoiceInfo | null
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function VoicePanel({ orbState, onVoice, onSpeak, voiceAvailable, settings, voiceInfo, onUpdate }: VoicePanelProps) {
  const [testText, setTestText] = useState('Hello, Sir. JARVIS systems online.')

  const groups = useMemo(() => {
    const catalog = voiceInfo?.catalog ?? []
    const map = new Map<string, { id: string; label: string }[]>()
    for (const v of catalog) {
      if (!map.has(v.group)) map.set(v.group, [])
      map.get(v.group)!.push({ id: v.id, label: v.label })
    }
    return Array.from(map.entries())
  }, [voiceInfo])

  const currentVoice = settings?.tts_voice || ''

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase">Voice Controls</h3>

      {/* Status strip */}
      <div className="flex items-center gap-2 flex-wrap text-[10px]">
        <span className="glass-panel px-2.5 py-1 flex items-center gap-1.5 text-slate-400">
          <AudioLines className="w-3 h-3 text-cyan-400/70" />
          Engine: <b className="text-slate-300">{voiceInfo?.engine || settings?.tts_engine || '—'}</b>
        </span>
        <span className="glass-panel px-2.5 py-1 flex items-center gap-1.5 text-slate-400">
          <Sparkles className="w-3 h-3 text-cyan-400/70" />
          Backend: <b className="text-slate-300">{voiceInfo?.backend || '—'}</b>
        </span>
        <span className="glass-panel px-2.5 py-1 text-slate-400">
          {voiceInfo?.catalog?.length || 0} voices available
        </span>
        <span className={`glass-panel px-2.5 py-1 flex items-center gap-1.5 ${voiceInfo?.mic_available ? 'text-emerald-400' : 'text-red-400'}`}>
          <Mic className="w-3 h-3" />
          Mic {voiceInfo?.mic_available ? 'ready' : 'unavailable'}
        </span>
      </div>

      {/* Microphone */}
      <div className="glass-panel p-5 flex flex-col items-center gap-3">
        <motion.div
          animate={{ scale: orbState === 'listening' ? [1, 1.08, 1] : 1 }}
          transition={{ repeat: orbState === 'listening' ? Infinity : 0, duration: 1.2 }}
        >
          <button
            onClick={onVoice}
            disabled={!voiceAvailable}
            className={`w-24 h-24 rounded-full flex items-center justify-center border-2 transition-all ${
              orbState === 'listening'
                ? 'border-cyan-400 bg-cyan-500/20 shadow-[0_0_40px_rgba(0,240,255,0.45)]'
                : 'border-cyan-500/30 bg-slate-800/80 hover:border-cyan-400/60'
            }`}
            title={voiceAvailable ? 'Click to speak' : 'Microphone unavailable'}
          >
            {orbState === 'listening' ? (
              <MicOff className="w-9 h-9 text-cyan-400" />
            ) : (
              <Mic className="w-9 h-9 text-cyan-400" />
            )}
          </button>
        </motion.div>
        <div className="text-xs text-slate-400">
          {orbState === 'listening' ? 'Listening... speak now' : 'Hold to talk, or press Ctrl+Space'}
        </div>
      </div>

      {/* Voice picker */}
      <div className="glass-panel p-3 space-y-2">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Sparkles className="w-4 h-4 text-cyan-400/70" />
          Voice
        </div>
        <select
          value={currentVoice}
          onChange={(e) => onUpdate({ tts_voice: e.target.value })}
          className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-400/60"
        >
          {groups.length === 0 && <option value={currentVoice}>{currentVoice || 'default'}</option>}
          {groups.map(([group, voices]) => (
            <optgroup key={group} label={group}>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>{v.label} ({v.id})</option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {/* Speed / volume */}
      <div className="glass-panel p-3 space-y-3">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Gauge className="w-4 h-4 text-cyan-400/70" />
          Speech Parameters
        </div>
        <Slider
          label="Speed (wpm)"
          min={80}
          max={500}
          value={settings?.tts_speed ?? 160}
          onChange={(v) => onUpdate({ tts_speed: v })}
        />
        <Slider
          label="Volume"
          min={0}
          max={100}
          value={settings?.tts_volume ?? 80}
          onChange={(v) => onUpdate({ tts_volume: v })}
        />
      </div>

      {/* Test TTS */}
      <div className="glass-panel p-3 space-y-2">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Volume2 className="w-4 h-4 text-cyan-400/70" />
          Test Speech
        </div>
        <input
          type="text"
          value={testText}
          onChange={(e) => setTestText(e.target.value)}
          placeholder="Text to speak..."
          className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60"
        />
        <button
          onClick={() => onSpeak(testText)}
          disabled={!testText.trim()}
          className="w-full px-3 py-1.5 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all disabled:opacity-50"
        >
          Speak
        </button>
      </div>
    </div>
  )
}
