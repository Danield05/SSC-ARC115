import type { ReactNode } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DEFAULT_THRESHOLDS, DISCLAIMER, getVitalInfo } from '../vitals/vitalInfo'
import type { AlertThresholds, VitalKey } from '../vitals/vitalInfo'

interface Props {
  /** Qué valor se explica. Se mantiene aunque la ventana esté cerrada para que no se vacíe al animar el cierre. */
  vital: VitalKey
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Umbrales del servidor; sin ellos se usan los valores por defecto. */
  thresholds?: AlertThresholds
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border p-4">
      <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      {children}
    </section>
  )
}

/** Ventana «Más información» de un valor: cómo se mide, referencias, alerta y qué hacer. */
export default function VitalInfoDialog({ vital, open, onOpenChange, thresholds = DEFAULT_THRESHOLDS }: Props) {
  const info = getVitalInfo(vital, thresholds)
  const Icon = info.icon

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] gap-5 overflow-y-auto p-5 sm:max-w-3xl sm:p-6">
        <DialogHeader className="gap-3 pr-8">
          <div className="flex items-center gap-3">
            <div className="bg-accent text-accent-foreground flex size-10 shrink-0 items-center justify-center rounded-lg">
              <Icon className="size-5" aria-hidden />
            </div>
            <DialogTitle className="text-xl leading-tight font-semibold">{info.dialogTitle}</DialogTitle>
          </div>
          <DialogDescription className="text-sm">{info.intro}</DialogDescription>
          <p className="text-muted-foreground text-xs">Cómo lo mide el dispositivo: {info.how}</p>
        </DialogHeader>

        <div className="grid gap-4 sm:grid-cols-2">
          <Panel title="Valores de referencia">
            <dl className="text-sm">
              {info.reference.rows.map((row) => (
                <div key={row.label} className="flex justify-between gap-4 border-b py-1.5 last:border-b-0">
                  <dt>{row.label}</dt>
                  <dd className="text-muted-foreground text-right tabular-nums">{row.value}</dd>
                </div>
              ))}
            </dl>
            <p className="text-muted-foreground mt-3 text-xs">{info.reference.note}</p>
          </Panel>
          <Panel title="Alerta">
            <Badge variant={info.alert.alert ? 'destructive' : 'secondary'}>{info.alert.badge}</Badge>
            <p className="text-muted-foreground mt-3 text-sm">{info.alert.text}</p>
          </Panel>
        </div>

        {info.sections.map((s) => (
          <Panel key={s.title} title={s.title}>
            <p className="text-muted-foreground text-sm">{s.text}</p>
          </Panel>
        ))}

        <div className="space-y-2 border-t pt-3">
          <p className="text-muted-foreground text-xs">Fuentes</p>
          <ul className="text-muted-foreground list-disc space-y-0.5 pl-5 text-xs">
            {info.sources.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <p className="text-muted-foreground text-xs">{DISCLAIMER}</p>
            <DialogClose render={<Button variant="outline" />}>Cerrar</DialogClose>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
