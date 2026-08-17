import { useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'

interface ParallaxPosition {
  x: number
  y: number
}

export function useParallax(depth: number = 1): ParallaxPosition {
  const [position, setPosition] = useState<ParallaxPosition>({ x: 0, y: 0 })

  const handleMouseMove = useCallback((e: MouseEvent) => {
    const { innerWidth, innerHeight } = window
    const x = (e.clientX / innerWidth - 0.5) * depth
    const y = (e.clientY / innerHeight - 0.5) * depth
    setPosition({ x, y })
  }, [depth])

  useEffect(() => {
    const isReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (isReduced) return

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [handleMouseMove])

  return position
}

export function ParallaxLayer({ depth = 1, children }: { depth?: number; children: ReactNode }) {
  const { x, y } = useParallax(depth)

  return (
    <div
      className="parallax-layer"
      style={{
        transform: `translate3d(${x}px, ${y}px, 0)`,
      }}
    >
      {children}
    </div>
  )
}
