import { useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface Props {
  /** Código del paciente que se edita; sin él, el formulario registra uno nuevo. */
  editing?: { code: string; name: string }
  onSubmit: (code: string, name: string) => Promise<void>
  onDone: () => void
}

export default function PatientForm({ editing, onSubmit, onDone }: Props) {
  const [code, setCode] = useState(editing?.code ?? '')
  const [name, setName] = useState(editing?.name ?? '')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onSubmit(code.trim(), name.trim())
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el paciente.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="patient-code">Código</Label>
        <Input
          id="patient-code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="P-0001"
          pattern="[A-Za-z0-9\-]{1,32}"
          title="Letras, números y guiones (máximo 32)"
          disabled={!!editing}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="patient-name">Nombre</Label>
        <Input id="patient-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} required />
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <Button type="submit" className="w-full" disabled={busy}>
        {busy ? 'Guardando…' : 'Guardar'}
      </Button>
    </form>
  )
}
