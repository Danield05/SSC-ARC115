import { CircleCheck, Inbox, Loader2, RefreshCw, TriangleAlert } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import PageHeader from '@/shared/components/PageHeader'
import { useAuth } from '../../auth/hooks/useAuth'
import { usePatients } from '../../patients/hooks/usePatients'
import { useUnassigned } from '../hooks/useUnassigned'
import { formatDateTime, formatNumber } from '../lib/format'
import { groupVisits, itemKey } from '../lib/unassigned'
import type { AssignResult } from '../types'

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

/**
 * Bandeja «Sin asignar»: mediciones que el aparato guardó sin paciente (por ejemplo, medidas sin
 * Wi-Fi) y que llegaron al sincronizar. Se agrupan por visita para asignarlas juntas.
 */
export default function UnassignedPage() {
  const { user } = useAuth()
  const canAssign = user?.role === 'admin' || user?.role === 'promoter'
  const { items, loading, error, reload, assign } = useUnassigned()
  const { patients } = usePatients()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [patientCode, setPatientCode] = useState('')
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState('')
  const [result, setResult] = useState<(AssignResult & { patient: string }) | null>(null)

  const visits = useMemo(() => groupVisits(items), [items])
  // Solo cuentan las elegidas que siguen en la bandeja (la lista se recarga tras asignar).
  const chosen = items.filter((m) => selected.has(itemKey(m)))
  const patientOptions = patients.map((p) => ({ value: p.patient_code, label: `${p.patient_code} · ${p.name || 'Sin nombre'}` }))

  function toggle(keys: string[], on: boolean) {
    setSelected((prev) => {
      const next = new Set(prev)
      for (const k of keys) {
        if (on) next.add(k)
        else next.delete(k)
      }
      return next
    })
  }

  async function submit() {
    setBusy(true)
    setFailure('')
    setResult(null)
    try {
      const outcome = await assign(
        patientCode,
        chosen.map((m) => ({ device_id: m.device_id, ts: m.ts })),
      )
      setResult({ ...outcome, patient: patientCode })
      setSelected(new Set())
    } catch (e) {
      setFailure(e instanceof Error ? e.message : 'No se pudieron asignar las mediciones.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Sin asignar"
        description="Mediciones que el aparato guardó sin paciente. Elige las de una visita, el paciente al que pertenecen y asígnalas."
        actions={
          <Button variant="outline" onClick={reload} disabled={loading}>
            <RefreshCw />
            Actualizar
          </Button>
        }
      />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {failure && (
        <Alert variant="destructive">
          <AlertDescription>{failure}</AlertDescription>
        </Alert>
      )}
      {result && (
        <Alert>
          <CircleCheck />
          <AlertDescription>
            {plural(result.assigned.length, 'medición asignada', 'mediciones asignadas')} a {result.patient}.
            {result.conflicts.length > 0 &&
              ` ${plural(result.conflicts.length, 'no se movió', 'no se movieron')}: ese paciente ya tenía una medición con la misma hora.`}
            {result.not_found.length > 0 &&
              ` ${plural(result.not_found.length, 'ya no estaba', 'ya no estaban')} disponible (otra persona la asignó).`}
          </AlertDescription>
        </Alert>
      )}
      {!canAssign && (
        <Alert>
          <AlertDescription>Tu rol es de solo lectura: puedes ver la bandeja, pero no asignar mediciones.</AlertDescription>
        </Alert>
      )}

      {canAssign && items.length > 0 && (
        <Card>
          <CardContent className="flex flex-wrap items-end gap-3 pt-6">
            <div className="min-w-64 flex-1 space-y-2">
              <Label>Paciente</Label>
              <Select items={patientOptions} value={patientCode || null} onValueChange={(v) => v && setPatientCode(v)}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={patientOptions.length ? 'Elige el paciente' : 'No hay pacientes registrados'} />
                </SelectTrigger>
                <SelectContent>
                  {patientOptions.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={submit} disabled={busy || !patientCode || chosen.length === 0}>
              {busy && <Loader2 className="animate-spin" />}
              Asignar {chosen.length > 0 ? `(${chosen.length})` : ''}
            </Button>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <p className="text-muted-foreground text-sm">Cargando…</p>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
            <div className="bg-accent text-accent-foreground flex size-12 items-center justify-center rounded-full">
              <Inbox className="size-6" />
            </div>
            <h2 className="text-lg font-semibold">No hay mediciones sin asignar</h2>
            <p className="text-muted-foreground max-w-md text-sm">
              Cuando el aparato mida sin una orden «Medir» (por ejemplo, sin Wi-Fi) y sincronice, las mediciones
              aparecerán aquí para asignarlas a su paciente.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-4">
          {visits.map((visit) => {
            const keys = visit.items.map(itemKey)
            const picked = keys.filter((k) => selected.has(k)).length
            const first = visit.items[visit.items.length - 1]
            const last = visit.items[0]
            return (
              <Card key={visit.key}>
                <CardHeader>
                  <div className="flex flex-wrap items-center gap-3">
                    {canAssign && (
                      <input
                        type="checkbox"
                        className="accent-primary size-4"
                        aria-label={`Elegir las ${visit.items.length} mediciones de esta visita`}
                        checked={picked === keys.length}
                        ref={(el) => {
                          if (el) el.indeterminate = picked > 0 && picked < keys.length
                        }}
                        onChange={(e) => toggle(keys, e.target.checked)}
                      />
                    )}
                    <div>
                      <CardTitle>
                        {visit.device_name || visit.device_id} · {formatDateTime(first.ts)}
                      </CardTitle>
                      <CardDescription>
                        {plural(visit.items.length, 'medición', 'mediciones')}
                        {visit.items.length > 1 && ` hasta ${formatDateTime(last.ts)}`} · {visit.device_id}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {canAssign && <TableHead className="w-10" />}
                        <TableHead>Fecha</TableHead>
                        <TableHead>Temperatura</TableHead>
                        <TableHead>SpO₂</TableHead>
                        <TableHead>Pulso</TableHead>
                        <TableHead>Peso</TableHead>
                        <TableHead>Estado</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {visit.items.map((m) => {
                        const key = itemKey(m)
                        return (
                          <TableRow key={key}>
                            {canAssign && (
                              <TableCell>
                                <input
                                  type="checkbox"
                                  className="accent-primary size-4"
                                  aria-label={`Elegir la medición del ${formatDateTime(m.ts)}`}
                                  checked={selected.has(key)}
                                  onChange={(e) => toggle([key], e.target.checked)}
                                />
                              </TableCell>
                            )}
                            <TableCell>{formatDateTime(m.ts)}</TableCell>
                            <TableCell className="tabular-nums">{formatNumber(m.temp_c, 1)} °C</TableCell>
                            <TableCell className="tabular-nums">{m.spo2} %</TableCell>
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
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </>
  )
}
