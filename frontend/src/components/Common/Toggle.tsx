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
          checked ? 'bg-cyan-500/30' : 'bg-slate-700'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 rounded-full transition-transform ${
            checked ? 'translate-x-6 bg-cyan-400' : 'translate-x-1 bg-slate-500'
          }`}
        />
      </button>
    </div>
  )
}
