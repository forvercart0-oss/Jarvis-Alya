import type { JarvisSettings } from '../../types'
import { Input, Slider } from '../Common'

interface AppearanceSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function AppearanceSettings({ settings, onUpdate }: AppearanceSettingsProps) {
  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Appearance</h3>
      <Input label="Theme" value={settings.theme} onChange={(v: string) => onUpdate({ theme: v })} placeholder="dark, light" />
      <Input label="Accent Color" value={settings.accent_color} onChange={(v: string) => onUpdate({ accent_color: v })} placeholder="#00f0ff" />
      <div>
        <label className="block text-xs text-slate-400 mb-1">Glow Intensity: {settings.glow_intensity}</label>
        <Slider min={0} max={100} value={settings.glow_intensity} onChange={(v: number) => onUpdate({ glow_intensity: v })} />
      </div>
      <Input label="Animation Level" value={settings.animation_level} onChange={(v: string) => onUpdate({ animation_level: v })} placeholder="low, medium, high" />
      <div>
        <label className="block text-xs text-slate-400 mb-1">Orb Size: {settings.orb_size}px</label>
        <Slider min={32} max={128} value={settings.orb_size} onChange={(v: number) => onUpdate({ orb_size: v })} />
      </div>
    </div>
  )
}
