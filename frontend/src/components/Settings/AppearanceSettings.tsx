import { useState, useEffect, useRef, useCallback } from 'react'
import type { JarvisSettings } from '../../types'
import { Input, Slider } from '../Common'

interface AppearanceSettingsProps {
  settings: JarvisSettings
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

export function AppearanceSettings({ settings, onUpdate }: AppearanceSettingsProps) {
  const [theme, setTheme] = useState(settings.theme)
  const [accentColor, setAccentColor] = useState(settings.accent_color)
  const [glowIntensity, setGlowIntensity] = useState(settings.glow_intensity)
  const [animationLevel, setAnimationLevel] = useState(settings.animation_level)
  const [orbSize, setOrbSize] = useState(settings.orb_size)
  const timersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({})

  useEffect(() => { setTheme(settings.theme) }, [settings.theme])
  useEffect(() => { setAccentColor(settings.accent_color) }, [settings.accent_color])
  useEffect(() => { setGlowIntensity(settings.glow_intensity) }, [settings.glow_intensity])
  useEffect(() => { setAnimationLevel(settings.animation_level) }, [settings.animation_level])
  useEffect(() => { setOrbSize(settings.orb_size) }, [settings.orb_size])

  const debouncedUpdate = useCallback((key: string, value: any) => {
    if (timersRef.current[key]) clearTimeout(timersRef.current[key])
    timersRef.current[key] = setTimeout(() => onUpdate({ [key]: value }), 300)
  }, [onUpdate])

  return (
    <div className="space-y-4 max-w-md">
      <h3 className="text-xs tracking-[0.3em] text-slate-400 uppercase mb-4">Appearance</h3>
      <Input label="Theme" value={theme} onChange={(v) => { setTheme(v); debouncedUpdate('theme', v) }} placeholder="dark, light" />
      <Input label="Accent Color" value={accentColor} onChange={(v) => { setAccentColor(v); debouncedUpdate('accent_color', v) }} placeholder="#00f0ff" />
      <div>
        <label className="block text-xs text-slate-400 mb-1">Glow Intensity: {glowIntensity}</label>
        <Slider min={0} max={100} value={glowIntensity} onChange={(v) => { setGlowIntensity(v); debouncedUpdate('glow_intensity', v) }} />
      </div>
      <Input label="Animation Level" value={animationLevel} onChange={(v) => { setAnimationLevel(v); debouncedUpdate('animation_level', v) }} placeholder="low, medium, high" />
      <div>
        <label className="block text-xs text-slate-400 mb-1">Orb Size: {orbSize}px</label>
        <Slider min={32} max={128} value={orbSize} onChange={(v) => { setOrbSize(v); debouncedUpdate('orb_size', v) }} />
      </div>
    </div>
  )
}
