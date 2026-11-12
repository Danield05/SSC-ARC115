import { CircleCheck, LineChart, Pencil, Plus, Search, X } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button, buttonVariants } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import PageHeader from '@/shared/components/PageHeader'
import { useAuth } from '../../auth/hooks/useAuth'
import PatientForm from '../components/PatientForm'
import { usePatients } from '../hooks/usePatients'
import { matchesPatient } from '../lib/search'
import type { Patient } from '../types'

const formatDate = (iso: string) =>
  iso ? new Date(iso).toLocaleString('es-SV', { dateStyle: 'medium', timeStyle: 'short' }) : '—'

export default function PatientsPage() {
  const { user } = useAuth()
  const canEdit = user?.role === 'admin' || user?.role === 'promoter'
  const { patients, loading, error, create, update } = usePatients()
  const [dialog, setDialog] = useState<{ editing?: Patient } | null>(null)
  const [notice, setNotice] = useState('')
  // La búsqueda vive en la URL (?q=): al volver desde el historial de un paciente sigue puesta.
  const [params, setParams] = useSearchParams()
  const query = params.get('q') ?? ''
  const setQuery = (value: string) => setParams(value ? { q: value } : {}, { replace: true })
  const shown = patients.filter((p) => matchesPatient(p, query))
  const searching = query.trim() !== ''

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

      {!loading && patients.length > 0 && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <div className="relative w-full max-w-md">
            <Search
              aria-hidden
              className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
            />
            <Input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar por nombre, apellido o código"
              aria-label="Buscar paciente por nombre, apellido o código"
              className="px-9 [&::-webkit-search-cancel-button]:hidden"
            />
            {searching && (
              <button
                type="button"
                onClick={() => setQuery('')}
                aria-label="Borrar la búsqueda"
                className="text-muted-foreground hover:text-foreground absolute top-1/2 right-2 flex size-6 -translate-y-1/2 items-center justify-center rounded-md"
              >
                <X className="size-4" />
              </button>
            )}
          </div>
          <p className="text-muted-foreground text-sm" aria-live="polite">
            {searching
              ? `${shown.length} de ${patients.length} pacientes`
              : `${patients.length} ${patients.length === 1 ? 'paciente' : 'pacientes'}`}
          </p>
        </div>
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
          ) : shown.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-12 text-center">
              <p className="text-muted-foreground max-w-md text-sm">
                Ningún paciente coincide con «{query.trim()}». Prueba con solo un nombre o un apellido, o con el
                código (por ejemplo P-0003).
              </p>
              <Button variant="outline" size="sm" onClick={() => setQuery('')}>
                Borrar la búsqueda
              </Button>
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
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shown.map((p) => (
                  <TableRow key={p.patient_code}>
                    <TableCell className="font-mono text-xs">{p.patient_code}</TableCell>
                    <TableCell>{p.name || <span className="text-muted-foreground">Sin nombre</span>}</TableCell>
                    <TableCell>{p.age ?? '—'}</TableCell>
                    <TableCell>{p.phone || '—'}</TableCell>
                    <TableCell>{formatDate(p.last_seen)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Link
                          to={`/patients/${encodeURIComponent(p.patient_code)}`}
                          className={buttonVariants({ variant: 'outline', size: 'sm' })}
                        >
                          <LineChart />
                          Historial
                        </Link>
                        {canEdit && (
                          <Button variant="outline" size="sm" onClick={() => setDialog({ editing: p })}>
                            <Pencil />
                            Editar
                          </Button>
                        )}
                      </div>
                    </TableCell>
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
