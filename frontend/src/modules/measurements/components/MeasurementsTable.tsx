import { TriangleAlert } from 'lucide-react'
import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { formatDateTime, formatNumber, spo2OutOfRange, tempOutOfRange } from '../lib/format'
import type { Measurement, Thresholds } from '../types'

const PAGE = 20

interface Props {
  /** De la más antigua a la más nueva; la tabla las muestra al revés. */
  items: Measurement[]
  thresholds: Thresholds
}

/** Los mismos datos de las gráficas en tabla: la forma de leerlos sin pasar el puntero. */
export default function MeasurementsTable({ items, thresholds }: Props) {
  const [shown, setShown] = useState(PAGE)
  const rows = [...items].reverse().slice(0, shown)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Mediciones</CardTitle>
        <CardDescription>Las más recientes primero. Los valores fuera de rango van en rojo.</CardDescription>
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
            {rows.map((m) => (
              <TableRow key={m.record_id}>
                <TableCell>{formatDateTime(m.ts)}</TableCell>
                <TableCell className={cn('tabular-nums', tempOutOfRange(m.temp_c, thresholds) && 'text-destructive font-medium')}>
                  {formatNumber(m.temp_c, 1)} °C
                </TableCell>
                <TableCell className={cn('tabular-nums', spo2OutOfRange(m.spo2, thresholds) && 'text-destructive font-medium')}>
                  {m.spo2} %
                </TableCell>
                <TableCell className="tabular-nums">{m.bpm} lpm</TableCell>
                <TableCell className="tabular-nums">{formatNumber(m.weight_kg, 1)} kg</TableCell>
                <TableCell>
                  {m.alert ? (
                    <Badge variant="destructive">
                      <TriangleAlert />
                      Alerta
                    </Badge>
                  ) : (
                    <Badge variant="outline">Normal</Badge>
                  )}
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
