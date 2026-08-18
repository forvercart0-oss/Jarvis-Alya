interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
  description?: string
  disabled?: boolean
}

export function Toggle({ checked, onChange, label, description, disabled = false }: ToggleProps) {
  return (
    <div className={`flex items-center justify-between ${disabled ? 'opacity-50' : ''}`}>
      <div>
        {label && <label className="text-sm text-slate-300">{label}</label>}
        {description && <p className="text-xs text-slate-500">{description}</p>}
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => !disabled && onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? 'bg-[var(--accent)]/30' : 'bg-slate-700'
        }`}
        style={checked ? { backgroundColor: 'color-mix(in srgb, var(--accent) 30%, transparent)' } : undefined}
      >
        <span
          className={`inline-block h-4 w-4 rounded-full transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-1 bg-slate-500'
          }`}
          style={checked ? { backgroundColor: 'var(--accent)' } : undefined}
        />
      </button>
    </div>
  )
}
