import { LineChart, Pencil, Plus } from 'lucide-react'
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
  const { patients, loading, error, create, rename } = usePatients()
  const [dialog, setDialog] = useState<{ editing?: Patient } | null>(null)

  return (
    <>
      <PageHeader
        title="Pacientes"
        description="Registra a cada paciente con su código y nombre. El dispositivo solo guarda el código."
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
                Registra un paciente con su código o espera a que un dispositivo sincronice sus primeras
                mediciones. Después podrás ponerle nombre y ver sus gráficas.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Código</TableHead>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Primera medición</TableHead>
                  <TableHead>Última medición</TableHead>
                  {canEdit && <TableHead className="text-right">Acciones</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {patients.map((p) => (
                  <TableRow key={p.patient_code}>
                    <TableCell className="font-mono text-xs">{p.patient_code}</TableCell>
                    <TableCell>{p.name || <span className="text-muted-foreground">Sin nombre</span>}</TableCell>
                    <TableCell>{formatDate(p.first_seen)}</TableCell>
                    <TableCell>{formatDate(p.last_seen)}</TableCell>
                    {canEdit && (
                      <TableCell className="text-right">
                        <Button variant="outline" size="sm" onClick={() => setDialog({ editing: p })}>
                          <Pencil />
                          Editar nombre
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
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{dialog?.editing ? 'Editar paciente' : 'Registrar paciente'}</DialogTitle>
            <DialogDescription>
              El nombre solo se guarda en el sistema web; el dispositivo y los correos usan el código.
            </DialogDescription>
          </DialogHeader>
          {dialog && (
            <PatientForm
              key={dialog.editing?.patient_code ?? 'nuevo'}
              editing={dialog.editing && { code: dialog.editing.patient_code, name: dialog.editing.name }}
              onSubmit={(code, name) => (dialog.editing ? rename(code, name) : create({ patient_code: code, name }))}
              onDone={() => setDialog(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
