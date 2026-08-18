import type { JarvisSettings, PersonaInfo } from '../../types'

interface PersonaSettingsProps {
  settings: JarvisSettings | null
  persona: PersonaInfo | null
  onSwitch: (personaId: string) => Promise<unknown>
}

const PERSONA_CARDS = [
  {
    id: 'jarvis',
    name: 'JARVIS',
    tagline: 'Masculine · cyan/blue',
    desc: 'Male persona. Speaks natural English with masculine Urdu/Hinglish: "Main karta hoon", "Main check karta hoon". Prefers a male Kokoro voice.',
    color: '#00f0ff',
  },
  {
    id: 'alya',
    name: 'ALYA',
    tagline: 'Feminine · pink/violet',
    desc: 'Female persona. Speaks natural English with feminine Urdu/Hinglish: "Main karti hoon", "Main check karti hoon". Prefers a female Kokoro voice.',
    color: '#ff6ec7',
  },
]

export function PersonaSettings({ settings, persona, onSwitch }: PersonaSettingsProps) {
  const active = persona?.id || settings?.persona || 'jarvis'

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm tracking-[0.2em] text-slate-400 uppercase mb-1">Persona</h3>
        <p className="text-xs text-slate-500">
          Switch between JARVIS and ALYA. The switch applies instantly — no restart needed. Voice, theme and system
          prompt change together.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PERSONA_CARDS.map((card) => {
          const isActive = active === card.id
          return (
            <button
              key={card.id}
              onClick={() => onSwitch(card.id)}
              className={[
                'text-left glass-panel p-4 transition-all rounded-lg border',
                isActive ? 'ring-2 ring-offset-0' : 'hover:bg-slate-800/40',
              ].join(' ')}
              style={isActive ? { borderColor: card.color, boxShadow: `0 0 20px ${card.color}22` } : undefined}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div
                    className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold"
                    style={{ background: `radial-gradient(circle, ${card.color}33, transparent)`, border: `1px solid ${card.color}66`, color: card.color }}
                  >
                    {card.name[0]}
                  </div>
                  <div>
                    <div className="text-sm font-semibold" style={{ color: card.color }}>
                      {card.name}
                    </div>
                    <div className="text-[10px] tracking-wider uppercase text-slate-500">{card.tagline}</div>
                  </div>
                </div>
                <div
                  className="w-3 h-3 rounded-full border"
                  style={{
                    borderColor: card.color,
                    background: isActive ? card.color : 'transparent',
                    boxShadow: isActive ? `0 0 10px ${card.color}` : 'none',
                  }}
                />
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{card.desc}</p>
            </button>
          )
        })}
      </div>

      {persona && (
        <div className="glass-panel p-4 space-y-3">
          <h4 className="text-[10px] tracking-[0.25em] uppercase text-slate-500">Active persona</h4>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <div className="text-slate-500 mb-0.5">Name</div>
              <div className="text-slate-300">{persona.name}</div>
            </div>
            <div>
              <div className="text-slate-500 mb-0.5">Gender</div>
              <div className="text-slate-300 capitalize">{persona.gender}</div>
            </div>
            <div>
              <div className="text-slate-500 mb-0.5">Voice</div>
              <div className="text-slate-300 font-mono">{persona.tts_voice || persona.default_voice}</div>
            </div>
            <div>
              <div className="text-slate-500 mb-0.5">Accent</div>
              <div className="text-slate-300 font-mono">{persona.accent_color}</div>
            </div>
          </div>
          <div className="pt-1">
            <span className="text-[10px] tracking-wider uppercase text-slate-500">
              Customize voice / theme in Appearance below
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
