import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'
import PulseLoader from './PulseLoader'

const FADE_MS = 500

/** Cubre la página con la animación de carga hasta que `ready` pasa a verdadero. */
export default function SplashScreen({ ready }: { ready: boolean }) {
  const [gone, setGone] = useState(ready)

  useEffect(() => {
    if (!ready) return
    const timer = setTimeout(() => setGone(true), FADE_MS)
    return () => clearTimeout(timer)
  }, [ready])

  if (gone) return null
  return (
    <div
      className={cn(
        'bg-background fixed inset-0 z-50 flex flex-col items-center justify-center gap-2 transition-opacity',
        ready ? 'pointer-events-none opacity-0' : 'opacity-100',
      )}
      style={{ transitionDuration: `${FADE_MS}ms` }}
    >
      <PulseLoader label="Preparando SSC-ARC115…" />
    </div>
  )
}
