import type { JarvisSettings } from '../../types'
import { Toggle } from '../Common'

interface MemorySettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function MemorySettings({ settings, onUpdate }: MemorySettingsProps) {
  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Memory</h3>
      <Toggle label="Memory Enabled" checked={settings.memory_enabled} onChange={(v: boolean) => onUpdate({ memory_enabled: v })} description="Enable persistent memory and context retention" />
      <Toggle label="Semantic Search" checked={!!settings.vector_memory_enabled} onChange={(v: boolean) => onUpdate({ vector_memory_enabled: v })} description="Index memories for vector recall (requires chromadb; falls back to keyword search)" />
    </div>
  )
}
