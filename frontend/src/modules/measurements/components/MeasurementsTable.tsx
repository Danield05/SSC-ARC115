import { TriangleAlert } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { formatDateTime, formatNumber, spo2OutOfRange, tempOutOfRange } from '../lib/format'
import { REVIEW_BADGE, REVIEW_LABEL } from '../lib/alerts'
import { deviationClass, deviationsOf } from '../lib/deviation'
import type { Measurement, Thresholds } from '../types'
import DeviationMark from './DeviationMark'

const PAGE = 20

interface Props {
  /** De la más antigua a la más nueva; la tabla las muestra al revés. */
  items: Measurement[]
  thresholds: Thresholds
}

/** Los mismos datos de las gráficas en tabla: la forma de leerlos sin pasar el puntero. */
export default function MeasurementsTable({ items, thresholds }: Props) {
  const [shown, setShown] = useState(PAGE)
  const deviations = useMemo(
    () => ({
      temp_c: deviationsOf(items, 'temp_c'),
      spo2: deviationsOf(items, 'spo2'),
      bpm: deviationsOf(items, 'bpm'),
      weight_kg: deviationsOf(items, 'weight_kg'),
    }),
    [items],
  )
  // Se conserva la posición de cada fila en la serie para buscar su desviación.
  const rows = items
    .map((m, i) => ({ m, i }))
    .reverse()
    .slice(0, shown)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Mediciones</CardTitle>
        <CardDescription>
          Las más recientes primero. Los valores fuera de rango van en rojo; el fondo y la flecha indican cuánto se alejan de las
          10 mediciones anteriores de esta persona (informativo, no diagnóstico).
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fecha</TableHead>
              <TableHead>Temperatura</TableHead>
              <TableHead>SpO₂</TableHead>
              <TableHead>Pulso</TableHead>
              <TableHead>Peso</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Dispositivo</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map(({ m, i }) => (
              <TableRow key={m.record_id}>
                <TableCell>{formatDateTime(m.ts)}</TableCell>
                <TableCell
                  className={cn(
                    'tabular-nums',
                    deviationClass(deviations.temp_c[i]),
                    tempOutOfRange(m.temp_c, thresholds) && 'text-destructive font-medium',
                  )}
                >
                  {formatNumber(m.temp_c, 1)} °C <DeviationMark deviation={deviations.temp_c[i]} />
                </TableCell>
                <TableCell
                  className={cn(
                    'tabular-nums',
                    deviationClass(deviations.spo2[i]),
                    spo2OutOfRange(m.spo2, thresholds) && 'text-destructive font-medium',
                  )}
                >
                  {m.spo2} % <DeviationMark deviation={deviations.spo2[i]} />
                </TableCell>
                <TableCell className={cn('tabular-nums', deviationClass(deviations.bpm[i]))}>
                  {m.bpm} lpm <DeviationMark deviation={deviations.bpm[i]} />
                </TableCell>
                <TableCell className={cn('tabular-nums', deviationClass(deviations.weight_kg[i]))}>
                  {formatNumber(m.weight_kg, 1)} kg <DeviationMark deviation={deviations.weight_kg[i]} />
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap items-center gap-1">
                    {m.alert ? (
                      <Badge variant="destructive">
                        <TriangleAlert />
                        Alerta
                      </Badge>
                    ) : (
                      <Badge variant="outline">Normal</Badge>
                    )}
                    {m.review && (
                      <Badge variant={REVIEW_BADGE[m.review.status]} title={m.review.note || undefined}>
                        {REVIEW_LABEL[m.review.status]}
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell className="font-mono text-xs">{m.device_id}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {items.length > shown && (
          <div className="flex justify-center border-t p-3">
            <Button variant="outline" size="sm" onClick={() => setShown((n) => n + PAGE)}>
              Mostrar más ({items.length - shown} restantes)
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
