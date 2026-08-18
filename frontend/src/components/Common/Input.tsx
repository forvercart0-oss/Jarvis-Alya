import { InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  label?: string
  error?: string
  onChange?: (value: string) => void
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({ label, error, onChange, className = '', ...props }, ref) => {
  return (
    <div className="space-y-1">
      {label && <label className="block text-xs text-slate-400">{label}</label>}
      <input
        ref={ref}
        onChange={(e) => onChange?.(e.target.value)}
        className={`w-full bg-slate-900/80 border ${error ? 'border-red-400/50' : 'border-[var(--accent)]/20'} rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none transition-all ${className}`}
        style={{ ['--tw-ring-color' as any]: 'var(--accent)' }}
        {...props}
      />
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  )
})

Input.displayName = 'Input'
