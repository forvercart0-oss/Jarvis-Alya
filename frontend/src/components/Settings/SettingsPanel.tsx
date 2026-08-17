import { useState } from 'react'
import type { JarvisSettings, PersonaInfo } from '../../types'
import { X } from 'lucide-react'
import { GeneralSettings } from './GeneralSettings'
import { AISettings } from './AISettings'
import { LocalAISettings } from './LocalAISettings'
import { VoiceSettings } from './VoiceSettings'
import { MemorySettings } from './MemorySettings'
import { AppearanceSettings } from './AppearanceSettings'
import { SecuritySettings } from './SecuritySettings'
import { AdvancedSettings } from './AdvancedSettings'
import { PersonaSettings } from './PersonaSettings'
import { MediaSettings } from './MediaSettings'
import { GestureSettings } from './GestureSettings'
import { CallSettings } from './CallSettings'
import { VisionSettings } from './VisionSettings'
import { WorkflowSettings } from './WorkflowSettings'
import { PersonalizationSettings } from './PersonalizationSettings'

interface SettingsPanelProps {
  settings: JarvisSettings | null
  persona: PersonaInfo | null
  onSwitchPersona: (personaId: string) => Promise<unknown>
  onUpdate: (patch: Partial<JarvisSettings>) => void
  onClose: () => void
}

type SettingsTab = 'general' | 'persona' | 'ai' | 'local_ai' | 'voice' | 'memory' | 'appearance' | 'security' | 'advanced' | 'media' | 'gestures' | 'calls' | 'vision' | 'workflows' | 'personalization'

export function SettingsPanel({ settings, persona, onSwitchPersona, onUpdate, onClose }: SettingsPanelProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')

  if (!settings) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500">
        Loading settings...
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-500/10">
        <h2 className="text-sm tracking-[0.2em] text-cyan-400/70 uppercase">Settings</h2>
        <button onClick={onClose} className="text-slate-500 hover:text-cyan-300 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-hidden flex">
        <div className="w-40 border-r border-cyan-500/10 py-2 px-1 space-y-0.5">
          {[
            { id: 'general', label: 'General' },
            { id: 'persona', label: 'Persona' },
            { id: 'ai', label: 'AI Models' },
            { id: 'local_ai', label: 'Local AI' },
            { id: 'voice', label: 'Voice' },
            { id: 'memory', label: 'Memory' },
            { id: 'appearance', label: 'Appearance' },
            { id: 'security', label: 'Security' },
            { id: 'advanced', label: 'Advanced' },
            { id: 'media', label: 'Media' },
            { id: 'gestures', label: 'Gestures' },
             { id: 'calls', label: 'Calls' },
             { id: 'vision', label: 'Vision' },
             { id: 'workflows', label: 'Workflows' },
             { id: 'personalization', label: 'Personalization' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as SettingsTab)}
              className={`w-full text-left px-3 py-1.5 text-xs rounded transition-colors ${
                activeTab === tab.id
                  ? 'text-cyan-400 bg-cyan-500/10'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'general' && <GeneralSettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'persona' && (
            <PersonaSettings settings={settings} persona={persona} onSwitch={onSwitchPersona} onUpdate={onUpdate} />
          )}
          {activeTab === 'ai' && <AISettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'local_ai' && <LocalAISettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'voice' && <VoiceSettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'memory' && <MemorySettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'appearance' && <AppearanceSettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'security' && <SecuritySettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'advanced' && <AdvancedSettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'media' && <MediaSettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'gestures' && <GestureSettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'calls' && <CallSettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'vision' && <VisionSettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'workflows' && <WorkflowSettings settings={settings} onUpdate={onUpdate} />}
          {activeTab === 'personalization' && <PersonalizationSettings settings={settings} onUpdate={onUpdate} />}
        </div>
      </div>
    </div>
  )
}
