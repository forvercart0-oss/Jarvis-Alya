import { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const base = 'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary: 'bg-cyan-500/15 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-400/25 hover:shadow-[0_0_14px_rgba(0,240,255,0.3)]',
    secondary: 'bg-slate-800 border border-slate-600/30 text-slate-300 hover:bg-slate-700',
    danger: 'bg-red-500/15 border border-red-400/40 text-red-300 hover:bg-red-400/25',
    ghost: 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50',
  }
  const sizes = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }

  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} disabled={disabled} {...props}>
      {children}
    </button>
  )
}
