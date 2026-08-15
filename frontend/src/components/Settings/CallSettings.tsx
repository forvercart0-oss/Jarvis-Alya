import type { JarvisSettings } from '../../types'

interface CallSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function CallSettings({ settings, onUpdate }: CallSettingsProps) {
  return (
    <div className="space-y-6 max-w-md">
      <div>
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-1">Call Control</h3>
        <p className="text-xs text-slate-500 mb-3">Manage calls through supported providers.</p>
        <label className="flex items-center gap-2 mb-3">
          <input
            type="checkbox"
            checked={settings.call_control_enabled ?? false}
            onChange={(e) => onUpdate({ call_control_enabled: e.target.checked })}
            className="accent-cyan-400"
          />
          <span className="text-xs text-slate-300">Enabled</span>
        </label>
        <div className="space-y-2">
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">Provider</label>
            <select
              value={settings.call_provider || ''}
              onChange={(e) => onUpdate({ call_provider: e.target.value })}
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400/40"
            >
              <option value="">None configured</option>
              <option value="browser">Browser Automation</option>
            </select>
          </div>
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">API Key (if required)</label>
            <input
              type="password"
              value={settings.call_api_key || ''}
              onChange={(e) => onUpdate({ call_api_key: e.target.value })}
              placeholder="Paste API key..."
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/40"
            />
          </div>
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">Assist Mode</label>
            <select
              value={settings.call_assist_mode || 'notify_only'}
              onChange={(e) => onUpdate({ call_assist_mode: e.target.value })}
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400/40"
            >
              <option value="notify_only">Notify Only</option>
              <option value="command_control">Command Control</option>
              <option value="ai_assist">AI Assist (requires explicit activation)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}
