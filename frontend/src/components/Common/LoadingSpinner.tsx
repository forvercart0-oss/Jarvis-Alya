export function LoadingSpinner({ size = 40, color = '#00f0ff' }: { size?: number; color?: string }) {
  return (
    <div className="flex items-center justify-center">
      <svg width={size} height={size} viewBox="0 0 50 50" className="animate-spin">
        <circle
          cx="25"
          cy="25"
          r="20"
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray="80"
          strokeDashoffset="60"
          opacity="0.3"
        />
        <circle
          cx="25"
          cy="25"
          r="20"
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray="80"
          strokeDashoffset="60"
          className="animate-spin"
          style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}
        />
      </svg>
    </div>
  )
}
