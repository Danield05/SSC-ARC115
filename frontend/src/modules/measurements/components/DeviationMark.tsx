import { ArrowDown, ArrowUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { deviationLabel } from '../lib/deviation'
import type { Deviation } from '../lib/deviation'

/** Flecha (y texto para lectores de pantalla) cuando el valor se aleja de su línea base. */
export default function DeviationMark({ deviation, className }: { deviation: Deviation | null; className?: string }) {
  if (!deviation || deviation.level === 'normal') return null
  const Icon = deviation.direction === 'down' ? ArrowDown : ArrowUp
  const label = deviationLabel(deviation)
  return (
    <span className={cn('inline-flex items-center', className)} title={label}>
      <Icon className={cn('size-4', deviation.level === 'deviation' && 'stroke-[3]')} aria-hidden />
      <span className="sr-only">{label}</span>
    </span>
  )
}
