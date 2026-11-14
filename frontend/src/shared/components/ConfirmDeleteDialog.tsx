import { Loader2, TriangleAlert } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  /** Qué se va a borrar y qué más se lleva consigo. */
  description: ReactNode
  /** Lo que hay que escribir para habilitar el botón (código, correo, «ELIMINAR»…). */
  confirmWord: string
  /** Texto del botón rojo. */
  confirmLabel?: string
  /** Borra de verdad; si lanza, el mensaje se muestra dentro del diálogo y no se cierra. */
  onConfirm: () => Promise<void>
}

const same = (a: string, b: string) => a.trim().toLowerCase() === b.trim().toLowerCase()

function Body({ title, description, confirmWord, confirmLabel, onConfirm, onCancel }: Omit<Props, 'open' | 'onOpenChange'> & { onCancel: () => void }) {
  const [typed, setTyped] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const ready = same(typed, confirmWord)

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!ready || busy) return
    setBusy(true)
    setError('')
    try {
      await onConfirm()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo eliminar.')
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription render={<div />}>{description}</DialogDescription>
      </DialogHeader>

      <Alert variant="destructive">
        <TriangleAlert />
        <AlertDescription>
          ¿Está seguro? Esta acción no se puede deshacer: estos datos no se podrán recuperar.
        </AlertDescription>
      </Alert>

      <div className="space-y-2">
        <Label htmlFor="confirm-word">
          Para continuar, escriba <span className="font-mono font-semibold">{confirmWord}</span>
        </Label>
        <Input
          id="confirm-word"
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          autoComplete="off"
          autoFocus
          disabled={busy}
          aria-invalid={typed !== '' && !ready}
        />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel} disabled={busy}>
          Cancelar
        </Button>
        <Button type="submit" variant="destructive" disabled={!ready || busy}>
          {busy && <Loader2 className="animate-spin" />}
          {confirmLabel ?? 'Eliminar'}
        </Button>
      </DialogFooter>
    </form>
  )
}

/**
 * Confirmación para borrar datos: avisa que no se pueden recuperar y no habilita el botón hasta
 * que se escribe la palabra clave (el código del aparato, el correo del usuario, «ELIMINAR»…).
 */
export default function ConfirmDeleteDialog({ open, onOpenChange, ...rest }: Props) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        {/* Se monta solo mientras está abierto: cada vez empieza con el campo vacío. */}
        {open && (
          <Body
            {...rest}
            onConfirm={async () => {
              await rest.onConfirm()
              onOpenChange(false)
            }}
            onCancel={() => onOpenChange(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}
