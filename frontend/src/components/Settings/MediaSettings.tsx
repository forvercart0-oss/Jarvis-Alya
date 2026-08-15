import type { JarvisSettings } from '../../types'

interface MediaSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function MediaSettings({ settings, onUpdate }: MediaSettingsProps) {
  return (
    <div className="space-y-6 max-w-md">
      <div>
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-1">Image Generation</h3>
        <p className="text-xs text-slate-500 mb-3">Generate images using AI providers.</p>
        <label className="flex items-center gap-2 mb-3">
          <input
            type="checkbox"
            checked={settings.image_generation_enabled ?? true}
            onChange={(e) => onUpdate({ image_generation_enabled: e.target.checked })}
            className="accent-cyan-400"
          />
          <span className="text-xs text-slate-300">Enabled</span>
        </label>
        <div className="space-y-2">
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">Provider</label>
            <select
              value={settings.image_provider || 'auto'}
              onChange={(e) => onUpdate({ image_provider: e.target.value })}
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400/40"
            >
              <option value="auto">Auto</option>
              <option value="puter">Puter (Free)</option>
              <option value="pixazo">Pixazo (Free Tier)</option>
              <option value="gemini">Gemini</option>
            </select>
          </div>
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">Pixazo API Key</label>
            <input
              type="password"
              value={settings.pixazo_api_key || ''}
              onChange={(e) => onUpdate({ pixazo_api_key: e.target.value })}
              placeholder="Paste API key..."
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/40"
            />
          </div>
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">Puter API Key (optional)</label>
            <input
              type="password"
              value={settings.puter_api_key || ''}
              onChange={(e) => onUpdate({ puter_api_key: e.target.value })}
              placeholder="Paste API key..."
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/40"
            />
          </div>
        </div>
      </div>

      <div className="border-t border-cyan-500/10 pt-4">
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-1">Video Generation</h3>
        <p className="text-xs text-slate-500 mb-3">Generate videos using AI providers.</p>
        <label className="flex items-center gap-2 mb-3">
          <input
            type="checkbox"
            checked={settings.video_generation_enabled ?? true}
            onChange={(e) => onUpdate({ video_generation_enabled: e.target.checked })}
            className="accent-cyan-400"
          />
          <span className="text-xs text-slate-300">Enabled</span>
        </label>
        <div className="space-y-2">
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">Provider</label>
            <select
              value={settings.video_provider || 'auto'}
              onChange={(e) => onUpdate({ video_provider: e.target.value })}
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400/40"
            >
              <option value="auto">Auto</option>
              <option value="fal">fal.ai</option>
              <option value="magic_hour">Magic Hour</option>
            </select>
          </div>
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">fal.ai API Key</label>
            <input
              type="password"
              value={settings.fal_api_key || ''}
              onChange={(e) => onUpdate({ fal_api_key: e.target.value })}
              placeholder="Paste API key..."
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/40"
            />
          </div>
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">Magic Hour API Key</label>
            <input
              type="password"
              value={settings.magic_hour_api_key || ''}
              onChange={(e) => onUpdate({ magic_hour_api_key: e.target.value })}
              placeholder="Paste API key..."
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/40"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
