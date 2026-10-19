import { Plus } from 'lucide-react'
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
import { ROLE_LABELS } from '../../auth/types'
import UserForm from '../components/UserForm'
import { useUsers } from '../hooks/useUsers'

export default function UsersPage() {
  const { user: me } = useAuth()
  const { users, loading, error, create, setActive } = useUsers()
  const [actionError, setActionError] = useState('')
  const [open, setOpen] = useState(false)

  async function toggle(email: string, active: boolean) {
    setActionError('')
    try {
      await setActive(email, active)
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'La acción falló.')
    }
  }

  return (
    <>
      <PageHeader
        title="Usuarios"
        description="Administradores, promotores y evaluadores con acceso al sistema."
        actions={
          <Button onClick={() => setOpen(true)}>
            <Plus />
            Nuevo usuario
          </Button>
        }
      />

      {(error || actionError) && (
        <Alert variant="destructive">
          <AlertDescription>{error || actionError}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-muted-foreground p-6 text-sm">Cargando…</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Correo</TableHead>
                  <TableHead>Rol</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acceso</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.email}>
                    <TableCell>
                      {u.email}
                      {u.email === me?.email && <span className="text-muted-foreground ml-2 text-xs">(tú)</span>}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{ROLE_LABELS[u.role]}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={u.active ? 'default' : 'secondary'}>{u.active ? 'Activo' : 'Desactivado'}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {u.email !== me?.email && (
                        <Switch
                          checked={u.active}
                          onCheckedChange={(checked) => toggle(u.email, checked)}
                          aria-label={`${u.active ? 'Desactivar' : 'Activar'} a ${u.email}`}
                        />
                      )}
                    </TableCell>
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
            <DialogTitle>Nuevo usuario</DialogTitle>
            <DialogDescription>El usuario podrá entrar con este correo y contraseña.</DialogDescription>
          </DialogHeader>
          <UserForm onCreate={create} onDone={() => setOpen(false)} />
        </DialogContent>
      </Dialog>
    </>
  )
}
