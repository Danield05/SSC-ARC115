import { Info } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface Props {
  title: string
  value: string
  hint: string
  icon: LucideIcon
  /** Resalta el valor cuando está fuera de rango. */
  alert?: boolean
  /** Si se pasa, muestra un botón «Más información» junto al icono. */
  onInfo?: () => void
}

/** Tarjeta con un dato destacado (etiqueta, valor y una línea de contexto). */
export default function StatCard({ title, value, hint, icon: Icon, alert, onInfo }: Props) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardDescription>{title}</CardDescription>
        <div className="flex items-center gap-1">
          {onInfo && (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-haspopup="dialog"
              aria-label={`Más información sobre ${title}`}
              onClick={onInfo}
            >
              <Info className="text-muted-foreground" />
            </Button>
          )}
          <div className="bg-accent text-accent-foreground flex size-8 items-center justify-center rounded-lg">
            <Icon className="size-4" />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className={cn('text-3xl font-semibold tracking-tight', alert && 'text-destructive')}>{value}</p>
        <p className="text-muted-foreground mt-1 text-xs">{hint}</p>
      </CardContent>
    </Card>
  )
}
