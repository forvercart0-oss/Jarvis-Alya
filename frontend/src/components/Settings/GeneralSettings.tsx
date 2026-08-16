import type { JarvisSettings } from '../../types'
import { Input, Toggle } from '../Common'

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

      <div className="pt-4 border-t border-cyan-500/10">
        <h4 className="text-xs tracking-[0.2em] text-slate-500 uppercase mb-3">Notifications</h4>
        <Toggle label="Message Notifications" checked={safeGet(settings, 'message_notifications_enabled', true)} onChange={(v: boolean) => onUpdate({ message_notifications_enabled: v })} />
        <Toggle label="Browser Notifications" checked={safeGet(settings, 'browser_notifications_enabled', true)} onChange={(v: boolean) => onUpdate({ browser_notifications_enabled: v })} />
        <Toggle label="Voice Notifications" checked={safeGet(settings, 'voice_notifications_enabled', true)} onChange={(v: boolean) => onUpdate({ voice_notifications_enabled: v })} />
        <Toggle label="Desktop Notifications" checked={safeGet(settings, 'desktop_notifications_enabled', true)} onChange={(v: boolean) => onUpdate({ desktop_notifications_enabled: v })} />
      </div>
    </div>
  )
}

function safeGet(obj: any, key: string, fallback: any) {
  return obj && Object.prototype.hasOwnProperty.call(obj, key) ? obj[key] : fallback
}
