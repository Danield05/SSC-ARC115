import { ArrowDown, ArrowUp, TriangleAlert } from 'lucide-react'
import { useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { deviationLabel, deviationsOf } from '../lib/deviation'
import type { Deviation } from '../lib/deviation'
import { formatDate, formatDateTime, formatNumber } from '../lib/format'
import type { Measurement, Variable } from '../types'

const ROWS: { key: Variable; label: string; unit: string; decimals: number }[] = [
  { key: 'temp_c', label: 'Temperatura', unit: '°C', decimals: 1 },
  { key: 'spo2', label: 'SpO₂', unit: '%', decimals: 0 },
  { key: 'bpm', label: 'Pulso', unit: 'lpm', decimals: 0 },
  { key: 'weight_kg', label: 'Peso', unit: 'kg', decimals: 1 },
]

/** Con más celdas que estas ya no cabe una flecha dentro de cada una. */
const MAX_WITH_ARROWS = 60
/** Ancho mínimo de una celda: pasado esto la franja se desplaza en horizontal. */
const MIN_CELL_PX = 10

const FILL = {
  normal: 'bg-muted',
  attention: 'bg-warning/60',
  deviation: 'bg-destructive/60',
}

function Swatch({ className, children }: { className: string; children?: React.ReactNode }) {
  return (
    <span className={cn('flex h-4 w-5 items-center justify-center rounded-[2px]', className)} aria-hidden>
      {children}
    </span>
  )
}

function counts(devs: (Deviation | null)[]) {
  const attention = devs.filter((d) => d?.level === 'attention').length
  const deviation = devs.filter((d) => d?.level === 'deviation').length
  return { attention, deviation }
}

/**
 * Franja de desviación: una fila por parámetro y una celda por medición, de la más antigua a la
 * más nueva. El color dice cuánto se aleja el valor de las 10 mediciones anteriores de esa
 * persona y la flecha hacia dónde. La idea (colorear cada punto según lo común que fue su valor
 * en la ventana previa) viene de Data Chromatix, de PhysioNet; solo se toma el método.
 */
export default function DeviationStrip({ items }: { items: Measurement[] }) {
  const rows = useMemo(
    () => ROWS.map((row) => ({ ...row, devs: deviationsOf(items, row.key) })),
    [items],
  )
  const dense = items.length > MAX_WITH_ARROWS
  const first = items[0]
  const last = items.at(-1)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Franja de desviación</CardTitle>
        <CardDescription>
          Una celda por medición, en orden. El color indica cuánto se aleja cada valor de las 10 mediciones anteriores de esta
          persona y la flecha hacia dónde. Informativo: no es un umbral clínico ni un diagnóstico.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="overflow-x-auto">
          <div className="space-y-1.5" style={{ minWidth: items.length * MIN_CELL_PX + 96 }}>
            <div className="flex items-center gap-2">
              <span className="w-20 shrink-0 text-xs font-medium sm:w-24">Alertas</span>
              <div
                className="flex flex-1 gap-px"
                role="img"
                aria-label={`Alertas: ${items.filter((m) => m.alert).length} de ${items.length} mediciones.`}
              >
                {items.map((m) => (
                  <div
                    key={m.record_id}
                    title={`${formatDateTime(m.ts)}${m.alert ? ' · alerta' : ''}`}
                    className={cn('flex h-6 flex-1 items-center justify-center rounded-[2px]', !m.alert && 'bg-muted/40')}
                  >
                    {m.alert && !dense && <TriangleAlert className="text-destructive size-3.5" aria-hidden />}
                    {m.alert && dense && <span className="bg-destructive h-full w-full rounded-[2px]" aria-hidden />}
                  </div>
                ))}
              </div>
            </div>

            {rows.map((row) => {
              const { attention, deviation } = counts(row.devs)
              return (
                <div key={row.key} className="flex items-center gap-2">
                  <span className="w-20 shrink-0 text-xs font-medium sm:w-24">{row.label}</span>
                  <div
                    className="flex flex-1 gap-px"
                    role="img"
                    aria-label={`${row.label}: ${deviation} mediciones con desvío y ${attention} con algo de desvío, de ${items.length}.`}
                  >
                    {items.map((m, i) => {
                      const d = row.devs[i]
                      const Icon = d?.direction === 'down' ? ArrowDown : ArrowUp
                      const base = `${formatDateTime(m.ts)} · ${formatNumber(m[row.key], row.decimals)} ${row.unit}`
                      const note = d === null ? 'aún sin línea base' : deviationLabel(d)
                      return (
                        <div
                          key={m.record_id}
                          title={note ? `${base} · ${note}` : base}
                          className={cn(
                            'flex h-6 flex-1 items-center justify-center rounded-[2px]',
                            d === null ? 'border border-dashed border-border' : FILL[d.level],
                          )}
                        >
                          {d && d.level !== 'normal' && !dense && (
                            <Icon className={cn('text-foreground size-3 sm:size-3.5', d.level === 'deviation' && 'stroke-[3]')} aria-hidden />
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}

            {first && last && (
              <div className="text-muted-foreground flex justify-between gap-2 pl-[88px] text-xs sm:pl-[104px]">
                <span>{formatDate(first.ts)}</span>
                {items.length > 1 && <span>{formatDate(last.ts)}</span>}
              </div>
            )}
          </div>
        </div>

        <ul className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-xs" aria-label="Cómo leer la franja">
          <li className="flex items-center gap-1.5">
            <Swatch className="bg-muted" /> Normal
          </li>
          <li className="flex items-center gap-1.5">
            <Swatch className="bg-warning/60">
              <ArrowUp className="text-foreground size-3" />
            </Swatch>
            Algo fuera de su línea base
          </li>
          <li className="flex items-center gap-1.5">
            <Swatch className="bg-destructive/60">
              <ArrowDown className="text-foreground size-3 stroke-[3]" />
            </Swatch>
            Desvío (la flecha dice hacia dónde)
          </li>
          <li className="flex items-center gap-1.5">
            <Swatch className="border border-dashed border-border" /> Aún sin línea base (menos de 3 mediciones anteriores)
          </li>
        </ul>
      </CardContent>
    </Card>
  )
}
