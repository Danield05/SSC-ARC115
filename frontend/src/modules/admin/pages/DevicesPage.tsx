import { KeyRound, Plus } from 'lucide-react'
import { useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import PageHeader from '@/shared/components/PageHeader'
import { useAuth } from '../../auth/hooks/useAuth'
import ApiKeyNotice from '../components/ApiKeyNotice'
import DeviceForm from '../components/DeviceForm'
import { useDevices } from '../hooks/useDevices'

export default function DevicesPage() {
  const { user } = useAuth()
  const canEdit = user?.role === 'admin'
  const { devices, loading, error, create, setActive, rotate } = useDevices()
  const [shown, setShown] = useState<{ id: string; key: string } | null>(null)
  const [actionError, setActionError] = useState('')
  const [open, setOpen] = useState(false)

  async function run(action: () => Promise<void>) {
    setActionError('')
    try {
      await action()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'La acción falló.')
    }
  }

  const onRotate = (id: string) =>
    run(async () => {
      if (!window.confirm(`Se generará una clave nueva para ${id}. La anterior dejará de funcionar. ¿Continuar?`)) return
      setShown({ id, key: await rotate(id) })
    })

  return (
    <>
      <PageHeader
        title="Dispositivos"
        description={
          canEdit
            ? 'Registra los dispositivos y controla cuáles pueden enviar mediciones.'
            : 'Dispositivos registrados (solo lectura).'
        }
        actions={
          canEdit && (
            <Button onClick={() => setOpen(true)}>
              <Plus />
              Registrar dispositivo
            </Button>
          )
        }
      />

      {shown && <ApiKeyNotice deviceId={shown.id} apiKey={shown.key} onClose={() => setShown(null)} />}
      {(error || actionError) && (
        <Alert variant="destructive">
          <AlertDescription>{error || actionError}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-muted-foreground p-6 text-sm">Cargando…</p>
          ) : devices.length === 0 ? (
            <p className="text-muted-foreground p-6 text-sm">No hay dispositivos registrados.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Identificador</TableHead>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Promotor</TableHead>
                  <TableHead>Estado</TableHead>
                  {canEdit && <TableHead className="text-right">Acciones</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {devices.map((d) => (
                  <TableRow key={d.device_id}>
                    <TableCell className="font-mono text-xs">{d.device_id}</TableCell>
                    <TableCell>{d.name}</TableCell>
                    <TableCell>{d.promoter_email}</TableCell>
                    <TableCell>
                      <Badge variant={d.active ? 'default' : 'secondary'}>{d.active ? 'Activo' : 'Desactivado'}</Badge>
                    </TableCell>
                    {canEdit && (
                      <TableCell>
                        <div className="flex items-center justify-end gap-3">
                          <Switch
                            checked={d.active}
                            onCheckedChange={(checked) => run(() => setActive(d.device_id, checked))}
                            aria-label={`${d.active ? 'Desactivar' : 'Activar'} ${d.device_id}`}
                          />
                          <Button variant="outline" size="sm" onClick={() => onRotate(d.device_id)}>
                            <KeyRound />
                            Nueva clave
                          </Button>
                        </div>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Registrar dispositivo</DialogTitle>
            <DialogDescription>Se generará una clave para el firmware. Solo se muestra una vez.</DialogDescription>
          </DialogHeader>
          <DeviceForm
            onCreate={async (data) => {
              setShown({ id: data.device_id, key: await create(data) })
            }}
            onDone={() => setOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </>
  )
}
