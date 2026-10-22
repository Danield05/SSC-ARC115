import { HeartPulse } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  label?: string
  className?: string
}

/** Latido y línea de electrocardiograma animados: la marca del proyecto mientras algo carga. */
export default function PulseLoader({ label = 'Cargando…', className }: Props) {
  return (
    <div role="status" aria-live="polite" className={cn('flex flex-col items-center gap-4', className)}>
      <div className="bg-primary/10 text-primary flex size-16 items-center justify-center rounded-2xl">
        <HeartPulse className="heart-beat size-9" />
      </div>
      <svg viewBox="0 0 100 24" className="text-primary h-6 w-40" fill="none" aria-hidden="true">
        <path
          className="ecg-line"
          d="M0 12 H28 L34 4 L42 21 L49 2 L55 12 H100"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          pathLength="100"
        />
      </svg>
      <span className="text-muted-foreground text-sm">{label}</span>
    </div>
  )
}
