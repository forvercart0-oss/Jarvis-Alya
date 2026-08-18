import type { JarvisSettings } from '../../types'

interface AdvancedSettingsProps {
  settings: JarvisSettings
}

export function AdvancedSettings({ settings }: AdvancedSettingsProps) {
  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Advanced</h3>
      <div className="glass-panel p-3 text-xs text-slate-400">
        <div className="flex justify-between mb-1"><span>Assistant Name</span><span className="text-slate-300">{settings.assistant_name}</span></div>
        <div className="flex justify-between mb-1"><span>User Name</span><span className="text-slate-300">{settings.user_name}</span></div>
        <div className="flex justify-between mb-1"><span>GROQ Model</span><span className="text-slate-300">{settings.groq_model}</span></div>
        <div className="flex justify-between mb-1"><span>TTS Engine</span><span className="text-slate-300">{settings.tts_engine}</span></div>
        <div className="flex justify-between mb-1"><span>TTS Voice</span><span className="text-slate-300">{settings.tts_voice}</span></div>
        <div className="flex justify-between mb-1"><span>Theme</span><span className="text-slate-300">{settings.theme}</span></div>
        <div className="flex justify-between mb-1"><span>Animation Level</span><span className="text-slate-300">{settings.animation_level}</span></div>
        <div className="flex justify-between"><span>Orb Size</span><span className="text-slate-300">{settings.orb_size}px</span></div>
      </div>
    </div>
  )
}
