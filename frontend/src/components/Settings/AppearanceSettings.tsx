import { useState, useEffect, useRef, useCallback } from 'react'
import type { JarvisSettings } from '../../types'
import { Input, Slider } from '../Common'

interface AppearanceSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

const PRESET_COLORS = [
  { label: 'Cyan', value: '#00f0ff' },
  { label: 'Electric Blue', value: '#3b82f6' },
  { label: 'Emerald', value: '#10b981' },
  { label: 'Purple', value: '#8b5cf6' },
  { label: 'Amber', value: '#f59e0b' },
  { label: 'Rose', value: '#f43f5e' },
  { label: 'White', value: '#e2e8f0' },
  { label: 'Orange', value: '#f97316' },
]

const inputCls = 'w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 focus:shadow-[0_0_12px_rgba(0,240,255,0.15)] transition-all font-mono'

export function AppearanceSettings({ settings, onUpdate }: AppearanceSettingsProps) {
  const [theme, setTheme] = useState(settings.theme)
  const [accentColor, setAccentColor] = useState(settings.accent_color)
  const [glowIntensity, setGlowIntensity] = useState(settings.glow_intensity)
  const [animationLevel, setAnimationLevel] = useState(settings.animation_level)
  const [orbSize, setOrbSize] = useState(settings.orb_size)
  const timersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({})
  const colorInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { setTheme(settings.theme) }, [settings.theme])
  useEffect(() => { setAccentColor(settings.accent_color) }, [settings.accent_color])
  useEffect(() => { setGlowIntensity(settings.glow_intensity) }, [settings.glow_intensity])
  useEffect(() => { setAnimationLevel(settings.animation_level) }, [settings.animation_level])
  useEffect(() => { setOrbSize(settings.orb_size) }, [settings.orb_size])

  const debouncedUpdate = useCallback((key: string, value: any) => {
    if (timersRef.current[key]) clearTimeout(timersRef.current[key])
    timersRef.current[key] = setTimeout(() => onUpdate({ [key]: value }), 300)
  }, [onUpdate])

  const handleColorChange = useCallback((color: string) => {
    setAccentColor(color)
    debouncedUpdate('accent_color', color)
  }, [debouncedUpdate])

  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Appearance</h3>

      <Input label="Theme" value={theme} onChange={(v) => { setTheme(v); debouncedUpdate('theme', v) }} placeholder="dark, light" />

      <div>
        <label className="block text-xs text-slate-400 mb-1">Accent Color</label>
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded border border-slate-600/50 cursor-pointer shrink-0 relative overflow-hidden"
            style={{ backgroundColor: accentColor }}
            onClick={() => colorInputRef.current?.click()}
          >
            <input
              ref={colorInputRef}
              type="color"
              value={accentColor}
              onChange={(e) => handleColorChange(e.target.value)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
          </div>
          <input
            type="text"
            value={accentColor}
            onChange={(e) => handleColorChange(e.target.value)}
            placeholder="#00f0ff"
            className={inputCls}
          />
        </div>
        <div className="flex gap-1.5 mt-2">
          {PRESET_COLORS.map((preset) => (
            <button
              key={preset.value}
              onClick={() => handleColorChange(preset.value)}
              className={`w-5 h-5 rounded-full border-2 transition-all hover:scale-110 ${
                accentColor === preset.value
                  ? 'border-white shadow-[0_0_8px_var(--tw-shadow-color)]'
                  : 'border-slate-700 hover:border-slate-500'
              }`}
              style={{ backgroundColor: preset.value, '--tw-shadow-color': preset.value } as React.CSSProperties}
              title={preset.label}
            />
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs text-slate-400 mb-1">Glow Intensity: {glowIntensity}</label>
        <Slider min={0} max={100} value={glowIntensity} onChange={(v) => { setGlowIntensity(v); debouncedUpdate('glow_intensity', v) }} />
      </div>

      <div>
        <label className="block text-xs text-slate-400 mb-1">Animation Level</label>
        <div className="flex gap-2">
          {['low', 'medium', 'high'].map((level) => (
            <button
              key={level}
              onClick={() => { setAnimationLevel(level); debouncedUpdate('animation_level', level) }}
              className={`flex-1 py-2 rounded border text-xs transition-all ${
                animationLevel === level
                  ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-400'
                  : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:border-slate-600/50'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-xs text-slate-400 mb-1">Orb Size: {orbSize}px</label>
        <Slider min={32} max={128} value={orbSize} onChange={(v) => { setOrbSize(v); debouncedUpdate('orb_size', v) }} />
      </div>
    </div>
  )
}
