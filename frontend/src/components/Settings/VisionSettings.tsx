import type { JarvisSettings } from '../../types'

interface VisionSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function VisionSettings({ settings, onUpdate }: VisionSettingsProps) {
  return (
    <div className="space-y-4">
      <div className="text-xs tracking-[0.2em] text-cyan-400/70 uppercase mb-4">Vision</div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-300">Enable Vision</div>
            <div className="text-[10px] text-slate-500">Allow screen capture and analysis</div>
          </div>
          <button
            onClick={() => onUpdate({ vision_enabled: !settings.vision_enabled })}
            className={`px-3 py-1 text-[10px] rounded border transition-all ${
              settings.vision_enabled
                ? 'bg-emerald-500/20 border-emerald-400/40 text-emerald-300'
                : 'bg-slate-800 border-slate-600/30 text-slate-400'
            }`}
          >
            {settings.vision_enabled ? 'ON' : 'OFF'}
          </button>
        </div>

        <div>
          <label className="text-xs text-slate-400 block mb-1">Vision Provider</label>
          <select
            value={settings.vision_provider || ''}
            onChange={(e) => onUpdate({ vision_provider: e.target.value })}
            className="w-full px-2 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-cyan-500/50"
          >
            <option value="">None (Disabled)</option>
            <option value="mock">Mock (Testing)</option>
          </select>
        </div>

        <div>
          <label className="text-xs text-slate-400 block mb-1">Confidence Threshold: {((settings.vision_confidence_threshold ?? 0.7) * 100).toFixed(0)}%</label>
          <input
            type="range"
            min="0.5"
            max="0.99"
            step="0.01"
            value={settings.vision_confidence_threshold ?? 0.7}
            onChange={(e) => onUpdate({ vision_confidence_threshold: parseFloat(e.target.value) })}
            className="w-full"
          />
          <div className="flex justify-between text-[10px] text-slate-600 mt-1">
            <span>50%</span>
            <span>99%</span>
          </div>
        </div>

        <div>
          <label className="text-xs text-slate-400 block mb-1">Capture Hotkey</label>
          <input
            type="text"
            value={settings.vision_capture_hotkey || 'ctrl+shift+j'}
            onChange={(e) => onUpdate({ vision_capture_hotkey: e.target.value })}
            className="w-full px-2 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-cyan-500/50"
            placeholder="ctrl+shift+j"
          />
        </div>

        <div>
          <label className="text-xs text-slate-400 block mb-1">Max Retries</label>
          <input
            type="number"
            min="1"
            max="10"
            value={settings.vision_max_retries || 3}
            onChange={(e) => onUpdate({ vision_max_retries: parseInt(e.target.value) || 3 })}
            className="w-full px-2 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-cyan-500/50"
          />
        </div>

        <div>
          <label className="text-xs text-slate-400 block mb-1">Cache TTL (seconds)</label>
          <input
            type="number"
            min="0"
            max="300"
            value={settings.vision_cache_ttl || 30}
            onChange={(e) => onUpdate({ vision_cache_ttl: parseFloat(e.target.value) || 30 })}
            className="w-full px-2 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-cyan-500/50"
          />
        </div>
      </div>

      <div className="mt-6 p-3 bg-slate-900/50 border border-slate-700/50 rounded text-[10px] text-slate-500 space-y-1">
        <div className="font-semibold text-slate-400">Privacy Notice</div>
        <p>Screenshots are processed locally by default and are not stored permanently.</p>
        <p>Vision must be explicitly enabled. A visible indicator shows when vision is active.</p>
        <p>OCR and analysis results are not saved to memory automatically.</p>
      </div>
    </div>
  )
}
