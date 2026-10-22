import type { LucideIcon } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface Props {
  title: string
  value: string
  hint: string
  icon: LucideIcon
  /** Resalta el valor cuando está fuera de rango. */
  alert?: boolean
}

/** Tarjeta con un dato destacado (etiqueta, valor y una línea de contexto). */
export default function StatCard({ title, value, hint, icon: Icon, alert }: Props) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardDescription>{title}</CardDescription>
        <div className="bg-accent text-accent-foreground flex size-8 items-center justify-center rounded-lg">
          <Icon className="size-4" />
        </div>
      </CardHeader>
      <CardContent>
        <p className={cn('text-3xl font-semibold tracking-tight', alert && 'text-destructive')}>{value}</p>
        <p className="text-muted-foreground mt-1 text-xs">{hint}</p>
      </CardContent>
    </Card>
  )
}
