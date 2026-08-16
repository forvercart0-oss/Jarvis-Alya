import type { PrivacySettings } from '../../types'
import { Shield, Lock, Eye, EyeOff } from 'lucide-react'

interface MemoryPrivacyProps {
  privacy: PrivacySettings | null
  onSetMode: (mode: string) => void
}

export function MemoryPrivacy({ privacy, onSetMode }: MemoryPrivacyProps) {
  const mode = privacy?.privacy_mode || 'normal'

  return (
    <div className="space-y-4">
      <h4 className="text-xs tracking-widest text-slate-400 uppercase">Privacy Mode</h4>
      <div className="grid grid-cols-3 gap-2">
        {(['normal', 'private', 'incognito'] as const).map((m) => (
          <button
            key={m}
            onClick={() => onSetMode(m)}
            className={`px-3 py-2 rounded text-[10px] tracking-wider uppercase transition-all ${
              mode === m
                ? 'bg-cyan-500/20 border border-cyan-400/40 text-cyan-200'
                : 'bg-slate-800/50 border border-slate-600/20 text-slate-400 hover:bg-slate-800'
            }`}
          >
            {m === 'normal' && <Eye className="w-3 h-3 inline mr-1" />}
            {m === 'private' && <Lock className="w-3 h-3 inline mr-1" />}
            {m === 'incognito' && <EyeOff className="w-3 h-3 inline mr-1" />}
            {m}
          </button>
        ))}
      </div>
      <div className="glass-panel p-3 space-y-2 text-[10px] text-slate-400">
        <div className="flex items-center gap-2">
          <Shield className="w-3 h-3" />
          <span>Normal: Memory enabled, cloud sharing asks</span>
        </div>
        <div className="flex items-center gap-2">
          <Lock className="w-3 h-3" />
          <span>Private: No cloud sharing, local only</span>
        </div>
        <div className="flex items-center gap-2">
          <EyeOff className="w-3 h-3" />
          <span>Incognito: No memory writes, temporary conversation</span>
        </div>
      </div>
    </div>
  )
}
