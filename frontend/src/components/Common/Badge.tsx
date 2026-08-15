interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  size?: 'sm' | 'md'
}

export function Badge({ children, variant = 'default', size = 'sm' }: BadgeProps) {
  const variants = {
    default: 'text-slate-300 bg-slate-800/60 border-slate-600/30',
    success: 'text-green-400 bg-green-400/10 border-green-400/30',
    warning: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30',
    danger: 'text-red-400 bg-red-400/10 border-red-400/30',
    info: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/30',
  }
  const sizes = { sm: 'px-1.5 py-0.5 text-[10px]', md: 'px-2 py-1 text-xs' }

  return (
    <span className={`inline-flex items-center rounded border ${variants[variant]} ${sizes[size]}`}>
      {children}
    </span>
  )
}
