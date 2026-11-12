import { Wifi, WifiOff } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatDateTime } from '../lib/format'
import { batchSizes, delayMs, formatDelay, syncState } from '../lib/traceability'
import type { Measurement } from '../types'

const PAGE = 20

/** Por cada medición: cuándo se midió, cuándo llegó a la nube y si el dispositivo la guardó sin conexión. */
export default function TraceabilityTable({ items }: { items: Measurement[] }) {
  const [shown, setShown] = useState(PAGE)
  const sizes = useMemo(() => batchSizes(items), [items])
  const rows = [...items].reverse().slice(0, shown)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trazabilidad de cada medición</CardTitle>
        <CardDescription>
          Las más recientes primero. Hasta 5 minutos entre medir y llegar a la nube se considera enviada al momento; más
          tiempo significa que el dispositivo la guardó sin conexión y la envió cuando volvió internet. Las que llegan
          juntas forman un lote.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Medición</TableHead>
              <TableHead>Llegó a la nube</TableHead>
              <TableHead>Retraso</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Lote</TableHead>
              <TableHead>Dispositivo</TableHead>
              <TableHead>Registro</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((m) => {
              const state = syncState(m)
              const delay = delayMs(m)
              const batch = m.received_at ? (sizes.get(m.received_at) ?? 1) : 0
              return (
                <TableRow key={m.record_id}>
                  <TableCell>{formatDateTime(m.ts)}</TableCell>
                  <TableCell>{m.received_at ? formatDateTime(m.received_at) : '—'}</TableCell>
                  <TableCell className="tabular-nums">{delay === null ? '—' : formatDelay(delay)}</TableCell>
                  <TableCell>
                    {state === 'offline' ? (
                      <Badge variant="secondary">
                        <WifiOff />
                        Sin conexión
                      </Badge>
                    ) : state === 'on_time' ? (
                      <Badge variant="outline">
                        <Wifi />
                        Al momento
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">Sin dato</span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {batch > 1 ? `Lote de ${batch}` : batch === 1 ? 'Individual' : '—'}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{m.device_id}</TableCell>
                  <TableCell className="font-mono text-xs">{m.record_id}</TableCell>
                </TableRow>
              )
            })}
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
