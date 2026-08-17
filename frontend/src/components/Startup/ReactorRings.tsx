import { motion } from 'framer-motion'

interface ReactorRingsProps {
  accentColor: string
  stage: 'idle' | 'starting' | 'active' | 'complete'
  reducedMotion?: boolean
}

export function ReactorRings({ accentColor, stage, reducedMotion }: ReactorRingsProps) {
  const rings = [
    { size: 160, delay: 0.3, rotateDuration: 20 },
    { size: 200, delay: 0.7, rotateDuration: 28 },
    { size: 260, delay: 1.1, rotateDuration: 36 },
  ]

  const ringVariants = {
    idle: { opacity: 0, scale: 0.8, rotate: 0 },
    starting: {
      opacity: 0.6,
      scale: 1,
      rotate: 360,
      transition: { duration: 20, repeat: Infinity, ease: 'linear' },
    },
    active: {
      opacity: 0.8,
      scale: 1,
      rotate: 360,
      transition: { duration: 20, repeat: Infinity, ease: 'linear' },
    },
    complete: { opacity: 0.9, scale: 1.05, rotate: 360, transition: { duration: 16, repeat: Infinity, ease: 'linear' } },
  }

  return (
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
      {rings.map((ring, i) => {
        const ringColor = stage === 'complete' ? accentColor : accentColor
        const opacity = stage === 'idle' ? 0 : stage === 'starting' ? 0.6 : 0.8

        if (reducedMotion) {
          return (
            <div
              key={i}
              className="absolute border rounded-full"
              style={{
                left: '50%',
                top: '50%',
                width: ring.size,
                height: ring.size,
                marginLeft: -ring.size / 2,
                marginTop: -ring.size / 2,
                borderColor: ringColor,
                opacity: stage === 'idle' ? 0 : opacity,
                transform: 'scale(1)',
              }}
            />
          )
        }

        return (
          <motion.div
            key={i}
            className="absolute border rounded-full"
            style={{
              left: '50%',
              top: '50%',
              width: ring.size,
              height: ring.size,
              marginLeft: -ring.size / 2,
              marginTop: -ring.size / 2,
              borderColor: ringColor,
              boxShadow: `0 0 8px ${ringColor}40`,
            }}
            initial={{ opacity: 0, scale: 0.7, rotate: 0 }}
            animate={stage === 'idle' ? 'idle' : stage === 'starting' ? 'starting' : stage === 'active' ? 'active' : 'complete'}
            variants={ringVariants}
            transition={{
              opacity: { duration: 0.5 },
              scale: { duration: 0.5 },
              rotate: { duration: ring.rotateDuration, repeat: Infinity, ease: 'linear' },
            }}
          />
        )
      })}
    </div>
  )
}
