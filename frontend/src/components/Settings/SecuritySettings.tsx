import type { JarvisSettings } from '../../types'

interface SecuritySettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

interface PermissionItem {
  id: string
  label: string
  description: string
  enabled: boolean
  level: 'allowed' | 'confirmation' | 'disabled'
  toggleable?: boolean
}

export function SecuritySettings({ settings, onUpdate }: SecuritySettingsProps) {
  const permissions: PermissionItem[] = [
    {
      id: 'microphone',
      label: 'Microphone',
      description: 'Allow JARVIS to access your microphone for voice input.',
      enabled: settings.voice_enabled,
      level: settings.voice_enabled ? 'allowed' : 'disabled',
      toggleable: true,
    },
    {
      id: 'camera',
      label: 'Camera',
      description: 'Allow JARVIS to access your camera for gesture control.',
      enabled: settings.gesture_control_enabled ?? false,
      level: (settings.gesture_control_enabled ?? false) ? 'allowed' : 'disabled',
      toggleable: true,
    },
    {
      id: 'notifications',
      label: 'Notifications',
      description: 'Show desktop notifications for messages and system events.',
      enabled: settings.desktop_notifications_enabled ?? true,
      level: (settings.desktop_notifications_enabled ?? true) ? 'allowed' : 'disabled',
      toggleable: false,
    },
    {
      id: 'computer_control',
      label: 'Computer Control',
      description: 'Allow JARVIS to control keyboard, mouse, and applications.',
      enabled: true,
      level: 'allowed',
      toggleable: false,
    },
    {
      id: 'browser_control',
      label: 'Browser Control',
      description: 'Allow JARVIS to interact with web browsers.',
      enabled: true,
      level: 'allowed',
      toggleable: false,
    },
    {
      id: 'messages',
      label: 'Messages',
      description: 'Allow JARVIS to read and draft messages. Requires confirmation for sending.',
      enabled: settings.message_notifications_enabled ?? false,
      level: (settings.message_notifications_enabled ?? false) ? 'confirmation' : 'disabled',
      toggleable: false,
    },
    {
      id: 'calls',
      label: 'Calls',
      description: 'Allow JARVIS to manage calls. Requires confirmation for outgoing calls.',
      enabled: settings.call_control_enabled ?? false,
      level: (settings.call_control_enabled ?? false) ? 'confirmation' : 'disabled',
      toggleable: true,
    },
  ]

  const togglePermission = (id: string) => {
    if (id === 'microphone') {
      onUpdate({ voice_enabled: !settings.voice_enabled })
    } else if (id === 'camera') {
      onUpdate({ gesture_control_enabled: !(settings.gesture_control_enabled ?? false) })
    } else if (id === 'calls') {
      onUpdate({ call_control_enabled: !(settings.call_control_enabled ?? false) })
    }
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'allowed': return 'text-green-400'
      case 'confirmation': return 'text-yellow-400'
      case 'disabled': return 'text-slate-600'
      default: return 'text-slate-500'
    }
  }

  const getLevelLabel = (level: string) => {
    switch (level) {
      case 'allowed': return 'Allowed'
      case 'confirmation': return 'Confirmation Required'
      case 'disabled': return 'Disabled'
      default: return level
    }
  }

  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Permissions</h3>
      <div className="space-y-3">
        {permissions.map((perm) => (
          <div key={perm.id} className="glass-panel p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-200">{perm.label}</div>
                <div className="text-[10px] text-slate-500">{perm.description}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] tracking-wider uppercase ${getLevelColor(perm.level)}`}>
                  {getLevelLabel(perm.level)}
                </span>
                {perm.toggleable && (
                  <button
                    onClick={() => togglePermission(perm.id)}
                    className={`w-10 h-5 rounded-full transition-all relative ${
                      perm.enabled ? 'bg-cyan-500/40' : 'bg-slate-700'
                    }`}
                  >
                    <div className={`absolute top-1 w-3 h-3 rounded-full bg-cyan-400 transition-all ${
                      perm.enabled ? 'left-6' : 'left-1'
                    }`} />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
