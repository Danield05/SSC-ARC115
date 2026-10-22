import { CircleCheck, LineChart, Pencil, Plus } from 'lucide-react'
import { useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import PageHeader from '@/shared/components/PageHeader'
import { useAuth } from '../../auth/hooks/useAuth'
import PatientForm from '../components/PatientForm'
import { usePatients } from '../hooks/usePatients'
import type { Patient } from '../types'

const formatDate = (iso: string) =>
  iso ? new Date(iso).toLocaleString('es-SV', { dateStyle: 'medium', timeStyle: 'short' }) : '—'

export default function PatientsPage() {
  const { user } = useAuth()
  const canEdit = user?.role === 'admin' || user?.role === 'promoter'
  const { patients, loading, error, create, update } = usePatients()
  const [dialog, setDialog] = useState<{ editing?: Patient } | null>(null)
  const [notice, setNotice] = useState('')

  return (
    <>
      <PageHeader
        title="Pacientes"
        description="Registra a cada paciente: el sistema le asigna un código automático. El dispositivo solo usa ese código."
        actions={
          canEdit && (
            <Button onClick={() => setDialog({})}>
              <Plus />
              Registrar paciente
            </Button>
          )
        }
      />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {notice && (
        <Alert>
          <CircleCheck />
          <AlertDescription>{notice}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-muted-foreground p-6 text-sm">Cargando…</p>
          ) : patients.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <div className="bg-accent text-accent-foreground flex size-12 items-center justify-center rounded-full">
                <LineChart className="size-6" />
              </div>
              <h2 className="text-lg font-semibold">Aún no hay pacientes</h2>
              <p className="text-muted-foreground max-w-md text-sm">
                Registra un paciente (el código se asigna solo) o espera a que un dispositivo sincronice sus
                primeras mediciones. Después podrás completar sus datos y ver sus gráficas.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Código</TableHead>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Edad</TableHead>
                  <TableHead>Teléfono</TableHead>
                  <TableHead>Última medición</TableHead>
                  {canEdit && <TableHead className="text-right">Acciones</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {patients.map((p) => (
                  <TableRow key={p.patient_code}>
                    <TableCell className="font-mono text-xs">{p.patient_code}</TableCell>
                    <TableCell>{p.name || <span className="text-muted-foreground">Sin nombre</span>}</TableCell>
                    <TableCell>{p.age ?? '—'}</TableCell>
                    <TableCell>{p.phone || '—'}</TableCell>
                    <TableCell>{formatDate(p.last_seen)}</TableCell>
                    {canEdit && (
                      <TableCell className="text-right">
                        <Button variant="outline" size="sm" onClick={() => setDialog({ editing: p })}>
                          <Pencil />
                          Editar
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialog !== null} onOpenChange={(open) => !open && setDialog(null)}>
        <DialogContent className="max-h-[90svh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{dialog?.editing ? 'Editar paciente' : 'Registrar paciente'}</DialogTitle>
            <DialogDescription>
              Los datos personales solo se guardan en el sistema web; el dispositivo y los correos usan el
              código.
            </DialogDescription>
          </DialogHeader>
          {dialog && (
            <PatientForm
              key={dialog.editing?.patient_code ?? 'nuevo'}
              editing={dialog.editing}
              onCreate={async (data) => {
                const created = await create(data)
                setNotice(`Paciente registrado con el código ${created.patient_code}.`)
              }}
              onUpdate={async (code, changes) => {
                await update(code, changes)
                setNotice(`Datos de ${code} actualizados.`)
              }}
              onDone={() => setDialog(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
