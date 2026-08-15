import type { JarvisSettings } from '../../types'
import { Input } from '../Common'

interface GeneralSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function GeneralSettings({ settings, onUpdate }: GeneralSettingsProps) {
  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">General</h3>
      <Input label="Assistant Name" value={settings.assistant_name} onChange={(v: string) => onUpdate({ assistant_name: v })} />
      <Input label="User Name" value={settings.user_name} onChange={(v: string) => onUpdate({ user_name: v })} />
      <Input label="Language" value={settings.language} onChange={(v: string) => onUpdate({ language: v })} />
      <Input label="Response Style" value={settings.response_style} onChange={(v: string) => onUpdate({ response_style: v })} placeholder="concise, detailed, creative" />
    </div>
  )
}
