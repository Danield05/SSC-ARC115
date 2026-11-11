import { MailCheck, Pencil, Plus, Send } from 'lucide-react'
import { useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import PageHeader from '@/shared/components/PageHeader'
import { useAuth } from '../../auth/hooks/useAuth'
import { ROLE_OPTIONS } from '../../auth/types'
import type { Role, User } from '../../auth/types'
import UserForm from '../components/UserForm'
import { useUsers } from '../hooks/useUsers'
import type { NewUser } from '../types'

export default function UsersPage() {
  const { user: me } = useAuth()
  const { users, loading, error, create, update, setActive, setRole, resend } = useUsers()
  const [actionError, setActionError] = useState('')
  const [notice, setNotice] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<User | null>(null)

  async function run(action: () => Promise<void>, success?: string) {
    setActionError('')
    setNotice('')
    try {
      await action()
      if (success) setNotice(success)
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'La acción falló.')
    }
  }

  async function invite(data: NewUser) {
    await create(data)
    setNotice(`Invitación enviada a ${data.email}. Recibirá una contraseña provisional por correo.`)
  }

  return (
    <>
      <PageHeader
        title="Usuarios"
        description="Invita a tu equipo: el sistema les envía una contraseña provisional y tú decides su rol."
        actions={
          <Button onClick={() => setOpen(true)}>
            <Plus />
            Invitar usuario
          </Button>
        }
      />

      {(error || actionError) && (
        <Alert variant="destructive">
          <AlertDescription>{error || actionError}</AlertDescription>
        </Alert>
      )}
      {notice && (
        <Alert>
          <MailCheck />
          <AlertDescription>{notice}</AlertDescription>
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
                  <TableHead>Persona</TableHead>
                  <TableHead>Rol</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acceso</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((u) => {
                  const isMe = u.email === me?.email
                  return (
                    <TableRow key={u.email}>
                      <TableCell>
                        <div className="font-medium">
                          {u.name || u.email}
                          {isMe && <span className="text-muted-foreground ml-2 text-xs font-normal">(tú)</span>}
                        </div>
                        {u.name && <div className="text-muted-foreground text-xs">{u.email}</div>}
                      </TableCell>
                      <TableCell>
                        {isMe ? (
                          <Badge variant="outline">{ROLE_OPTIONS.find((r) => r.value === u.role)?.label}</Badge>
                        ) : (
                          <Select
                            items={ROLE_OPTIONS}
                            value={u.role}
                            onValueChange={(v) => v && v !== u.role && run(() => setRole(u.email, v as Role))}
                          >
                            <SelectTrigger className="w-48" aria-label={`Rol de ${u.email}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {ROLE_OPTIONS.map((item) => (
                                <SelectItem key={item.value} value={item.value}>
                                  {item.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      </TableCell>
                      <TableCell>
                        {!u.active ? (
                          <Badge variant="secondary">Desactivado</Badge>
                        ) : u.must_change_password ? (
                          <Badge variant="outline" className="border-warning/60 text-warning-foreground">
                            Pendiente de verificar
                          </Badge>
                        ) : (
                          <Badge>Activo</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-3">
                          <Button variant="outline" size="sm" onClick={() => setEditing(u)}>
                            <Pencil />
                            Editar
                          </Button>
                          {!isMe && u.active && u.must_change_password && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                run(() => resend(u.email), `Se envió una contraseña provisional nueva a ${u.email}.`)
                              }
                            >
                              <Send />
                              Reenviar
                            </Button>
                          )}
                          {!isMe && (
                            <Switch
                              checked={u.active}
                              onCheckedChange={(checked) => run(() => setActive(u.email, checked))}
                              aria-label={`${u.active ? 'Desactivar' : 'Activar'} a ${u.email}`}
                            />
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invitar usuario</DialogTitle>
            <DialogDescription>Elige su rol: es lo que podrá ver y hacer dentro del sistema.</DialogDescription>
          </DialogHeader>
          <UserForm onCreate={invite} onUpdate={update} onDone={() => setOpen(false)} />
        </DialogContent>
      </Dialog>

      <Dialog open={editing !== null} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar usuario</DialogTitle>
            <DialogDescription>
              Cambia el nombre o el rol. El correo es su identificador y no se modifica.
            </DialogDescription>
          </DialogHeader>
          {editing && (
            <UserForm
              key={editing.email}
              editing={editing}
              isSelf={editing.email === me?.email}
              onCreate={async () => {}}
              onUpdate={update}
              onDone={() => setEditing(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
