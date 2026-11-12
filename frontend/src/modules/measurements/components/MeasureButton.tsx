import { Activity, CircleCheck, Loader2, TriangleAlert } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { listDevices } from '../../admin/api/adminApi'
import type { Device } from '../../admin/types'
import { useAuth } from '../../auth/hooks/useAuth'
import { useMeasureOrder } from '../hooks/useMeasureOrder'
import { formatDateTime } from '../lib/format'

/** Admin y promotor miden; el evaluador (viewer) solo lee. */
const MEASURERS = ['admin', 'promoter']

/**
 * Botón «Medir»: le deja una orden al aparato para que mida a este paciente. La medición llega ya
 * asignada; mientras tanto la ventana muestra en qué punto va. Sin Wi-Fi en el aparato no llega la
 * orden: en ese caso se mide con el botón OK del aparato y se asigna después en «Sin asignar».
 */
export default function MeasureButton({ code }: { code: string }) {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  if (!user || !MEASURERS.includes(user.role)) return null
  return (
    <>
      <Button onClick={() => setOpen(true)}>
        <Activity />
        Medir
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>{open && <MeasureFlow code={code} onClose={() => setOpen(false)} />}</DialogContent>
      </Dialog>
    </>
  )
}

function MeasureFlow({ code, onClose }: { code: string; onClose: () => void }) {
  const [devices, setDevices] = useState<Device[] | null>(null)
  const [loadError, setLoadError] = useState('')
  const [deviceId, setDeviceId] = useState('')
  const { order, error, busy, start, cancel, reset } = useMeasureOrder(deviceId, code)

  useEffect(() => {
    let cancelled = false
    listDevices()
      .then((all) => {
        if (cancelled) return
        const active = all.filter((d) => d.active)
        setDevices(active)
        if (active.length === 1) setDeviceId(active[0].device_id)
      })
      .catch((e) => {
        if (!cancelled) setLoadError(e instanceof Error ? e.message : 'No se pudieron cargar los dispositivos.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const status = order?.status
  const waiting = status === 'pendiente' || status === 'tomada'
  const options = (devices ?? []).map((d) => ({ value: d.device_id, label: `${d.name} (${d.device_id})` }))

  return (
    <>
      <DialogHeader>
        <DialogTitle>Medir a {code}</DialogTitle>
        <DialogDescription>
          El aparato recibe la orden por Wi-Fi y la medición queda guardada a nombre de este paciente.
        </DialogDescription>
      </DialogHeader>

      {loadError && (
        <Alert variant="destructive">
          <AlertDescription>{loadError}</AlertDescription>
        </Alert>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {devices !== null && devices.length === 0 && (
        <Alert>
          <AlertDescription>No hay dispositivos activos asignados a tu cuenta.</AlertDescription>
        </Alert>
      )}

      {!order && devices !== null && devices.length > 0 && (
        <div className="space-y-3">
          {options.length > 1 ? (
            <div className="space-y-2">
              <Label>Aparato</Label>
              <Select items={options} value={deviceId || null} onValueChange={(v) => v && setDeviceId(v)}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Elige el aparato" />
                </SelectTrigger>
                <SelectContent>
                  {options.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ) : (
            <p className="text-sm">
              Aparato: <span className="font-medium">{options[0]?.label}</span>
            </p>
          )}
          <p className="text-muted-foreground text-sm">
            Enciende el aparato y comprueba que tenga Wi-Fi. Puede tardar unos segundos en recibir la orden.
          </p>
        </div>
      )}

      {status === 'pendiente' && (
        <Progress title="Esperando al aparato…">
          La orden vence en 2 minutos. Si el aparato está apagado o sin Wi-Fi, mide con su botón OK y asigna después
          desde «Sin asignar».
        </Progress>
      )}
      {status === 'tomada' && (
        <Progress title="El aparato está midiendo">
          Sigue las indicaciones de su pantalla: peso, temperatura y oxímetro. Al terminar, pulsa OK en el aparato para
          guardar. Tiene 5 minutos.
        </Progress>
      )}
      {status === 'completada' && (
        <Alert>
          <CircleCheck />
          <AlertDescription>
            Medición recibida{order?.ts ? ` (${formatDateTime(order.ts)})` : ''}. Ya aparece en el historial de {code}.
          </AlertDescription>
        </Alert>
      )}
      {(status === 'expirada' || status === 'cancelada') && (
        <Alert>
          <TriangleAlert />
          <AlertDescription>
            {status === 'cancelada' ? 'La orden se canceló.' : 'No se recibió la medición a tiempo.'} Puedes intentarlo
            de nuevo. Si el aparato midió sin Wi-Fi, la medición aparecerá en «Sin asignar» cuando sincronice.
          </AlertDescription>
        </Alert>
      )}

      <DialogFooter>
        {waiting ? (
          <Button variant="outline" onClick={cancel} disabled={busy}>
            Cancelar orden
          </Button>
        ) : (
          <>
            <Button variant="outline" onClick={onClose}>
              Cerrar
            </Button>
            {status === 'completada' ? (
              <Button onClick={reset}>Medir otra vez</Button>
            ) : (
              <Button onClick={start} disabled={busy || !deviceId}>
                {busy && <Loader2 className="animate-spin" />}
                {status === undefined ? 'Enviar orden' : 'Intentar de nuevo'}
              </Button>
            )}
          </>
        )}
      </DialogFooter>
    </>
  )
}

function Progress({ title, children }: { title: string; children: string }) {
  return (
    <div role="status" aria-live="polite" className="flex items-start gap-3 rounded-lg border p-4">
      <Loader2 className="text-primary mt-0.5 size-5 shrink-0 animate-spin" />
      <div className="space-y-1">
        <p className="font-medium">{title}</p>
        <p className="text-muted-foreground text-sm">{children}</p>
      </div>
    </div>
  )
}
