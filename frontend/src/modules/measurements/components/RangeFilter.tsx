import { Button } from '@/components/ui/button'
import type { RangeDays } from '../types'

const OPTIONS: { label: string; days: RangeDays }[] = [
  { label: '7 días', days: 7 },
  { label: '30 días', days: 30 },
  { label: '90 días', days: 90 },
  { label: 'Todo', days: null },
]

interface Props {
  value: RangeDays
  onChange: (days: RangeDays) => void
}

/** Filtro de fechas: una sola fila sobre todo lo que filtra. */
export default function RangeFilter({ value, onChange }: Props) {
  return (
    <div role="group" aria-label="Rango de fechas" className="flex flex-wrap gap-2">
      {OPTIONS.map((o) => (
        <Button
          key={o.label}
          size="sm"
          variant={o.days === value ? 'default' : 'outline'}
          aria-pressed={o.days === value}
          onClick={() => onChange(o.days)}
        >
          {o.label}
        </Button>
      ))}
    </div>
  )
}
