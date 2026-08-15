import type { JarvisSettings } from '../../types'

interface GestureSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function GestureSettings({ settings, onUpdate }: GestureSettingsProps) {
  return (
    <div className="space-y-6 max-w-md">
      <div>
        <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-1">Gesture Control</h3>
        <p className="text-xs text-slate-500 mb-3">Control JARVIS with hand gestures using your camera.</p>
        <label className="flex items-center gap-2 mb-3">
          <input
            type="checkbox"
            checked={settings.gesture_control_enabled ?? false}
            onChange={(e) => onUpdate({ gesture_control_enabled: e.target.checked })}
            className="accent-cyan-400"
          />
          <span className="text-xs text-slate-300">Enabled</span>
        </label>
        <div className="space-y-2">
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">Camera Device</label>
            <input
              type="text"
              value={settings.gesture_camera_device || ''}
              onChange={(e) => onUpdate({ gesture_camera_device: e.target.value })}
              placeholder="/dev/video0 or leave empty for default"
              className="w-full bg-black/30 border border-cyan-500/20 rounded px-2 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/40"
            />
          </div>
          <div>
            <label className="block text-[10px] tracking-wider uppercase text-slate-500 mb-1">Sensitivity: {settings.gesture_sensitivity ?? 50}%</label>
            <input
              type="range"
              min="0"
              max="100"
              value={settings.gesture_sensitivity ?? 50}
              onChange={(e) => onUpdate({ gesture_sensitivity: parseInt(e.target.value) })}
              className="w-full accent-cyan-400"
            />
          </div>
        </div>
      </div>

      <div className="glass-panel p-3 space-y-1">
        <h4 className="text-[10px] tracking-[0.25em] uppercase text-slate-500 mb-2">Available Gestures</h4>
        {[
          { id: 'open_palm', name: 'Open Palm', action: 'Stop / Pause' },
          { id: 'thumbs_up', name: 'Thumbs Up', action: 'Confirm' },
          { id: 'thumbs_down', name: 'Thumbs Down', action: 'Cancel' },
          { id: 'point', name: 'Point', action: 'Select' },
          { id: 'two_fingers', name: 'Two Fingers', action: 'Scroll' },
          { id: 'pinch', name: 'Pinch', action: 'Click' },
          { id: 'fist', name: 'Fist', action: 'Stop Action' },
        ].map((g) => (
          <div key={g.id} className="flex justify-between text-xs">
            <span className="text-slate-400">{g.name}</span>
            <span className="text-slate-500">{g.action}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
