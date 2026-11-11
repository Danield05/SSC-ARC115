import { useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { NewPatient, Patient, PatientChanges } from '../types'

const SEX_OPTIONS = [
  { value: 'M', label: 'M · Masculino' },
  { value: 'F', label: 'F · Femenino' },
]

/** Máscara del DUI: 8 dígitos, guion automático y dígito verificador (01234567-8). */
function maskDui(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 9)
  return digits.length > 8 ? `${digits.slice(0, 8)}-${digits.slice(8)}` : digits
}

/** Máscara del teléfono: 8 dígitos con guion automático (7000-1234). */
function maskPhone(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 8)
  return digits.length > 4 ? `${digits.slice(0, 4)}-${digits.slice(4)}` : digits
}

interface Props {
  /** Paciente que se edita; sin él, el formulario registra uno nuevo. */
  editing?: Patient
  onCreate: (data: NewPatient) => Promise<void>
  onUpdate: (code: string, changes: PatientChanges) => Promise<void>
  onDone: () => void
}

export default function PatientForm({ editing, onCreate, onUpdate, onDone }: Props) {
  const [name, setName] = useState(editing?.name ?? '')
  const [dui, setDui] = useState(editing?.dui ?? '')
  const [age, setAge] = useState(editing?.age != null ? String(editing.age) : '')
  const [guardianName, setGuardianName] = useState(editing?.guardian_name ?? '')
  const [guardianDui, setGuardianDui] = useState(editing?.guardian_dui ?? '')
  const [phone, setPhone] = useState(editing?.phone ?? '')
  const [email, setEmail] = useState(editing?.email ?? '')
  const [address, setAddress] = useState(editing?.address ?? '')
  const [sex, setSex] = useState(editing?.sex ?? '')
  const [height, setHeight] = useState(editing?.height_cm != null ? String(editing.height_cm) : '')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // El DUI solo aplica a mayores de edad (18 años o más).
  const showDui = age !== '' && Number(age) >= 18
  const isMinor = age !== '' && Number(age) < 18

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!sex) {
      setError('Selecciona el sexo del paciente.')
      return
    }
    setBusy(true)
    setError('')
    const parsedAge = Number(age)
    const duiValue = parsedAge >= 18 ? dui.trim() : ''
    const guardianNameValue = parsedAge < 18 ? guardianName.trim() : ''
    const guardianDuiValue = parsedAge < 18 ? guardianDui.trim() : ''
    const parsedHeight = height.trim() === '' ? null : Number(height)
    try {
      if (editing) {
        await onUpdate(editing.patient_code, {
          name: name.trim(),
          // Un menor de 18 no puede tener DUI: se borra el que hubiera.
          dui: duiValue,
          guardian_name: guardianNameValue,
          guardian_dui: guardianDuiValue,
          age: parsedAge,
          email: email.trim(),
          phone: phone.trim(),
          address: address.trim(),
          sex,
          height_cm: parsedHeight,
        })
      } else {
        await onCreate({
          name: name.trim(),
          age: parsedAge,
          sex,
          ...(duiValue && { dui: duiValue }),
          ...(guardianNameValue && { guardian_name: guardianNameValue }),
          ...(guardianDuiValue && { guardian_dui: guardianDuiValue }),
          ...(email.trim() && { email: email.trim() }),
          ...(phone.trim() && { phone: phone.trim() }),
          ...(address.trim() && { address: address.trim() }),
          ...(parsedHeight !== null && { height_cm: parsedHeight }),
        })
      }
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el paciente.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="bg-muted/60 rounded-lg px-3 py-2 text-sm">
        <span className="text-muted-foreground">Código: </span>
        {editing ? (
          <span className="font-mono font-medium">{editing.patient_code}</span>
        ) : (
          <span className="text-muted-foreground">se asigna solo al guardar (P-0001, P-0002…)</span>
        )}
      </div>
      <div className="space-y-2">
        <Label htmlFor="patient-name">Nombre completo</Label>
        <Input
          id="patient-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={80}
          required
          autoFocus
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="patient-age">Edad</Label>
          <Input
            id="patient-age"
            type="number"
            min={0}
            max={120}
            required
            value={age}
            onChange={(e) => setAge(e.target.value)}
          />
        </div>
        {showDui && (
          <div className="space-y-2">
            <Label htmlFor="patient-dui">DUI</Label>
            <Input
              id="patient-dui"
              value={dui}
              onChange={(e) => setDui(maskDui(e.target.value))}
              placeholder="01234567-8"
              pattern="\d{8}-\d"
              title="Ocho dígitos, guion y el dígito verificador (01234567-8)"
              inputMode="numeric"
            />
          </div>
        )}
        {isMinor && (
          <>
            <div className="space-y-2">
              <Label htmlFor="patient-guardian-name">Nombre del responsable</Label>
              <Input
                id="patient-guardian-name"
                value={guardianName}
                onChange={(e) => setGuardianName(e.target.value)}
                maxLength={80}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="patient-guardian-dui">DUI del responsable</Label>
              <Input
                id="patient-guardian-dui"
                value={guardianDui}
                onChange={(e) => setGuardianDui(maskDui(e.target.value))}
                placeholder="01234567-8"
                pattern="\d{8}-\d"
                title="Ocho dígitos, guion y el dígito verificador (01234567-8)"
                inputMode="numeric"
                required
              />
            </div>
          </>
        )}
        <div className="space-y-2">
          <Label>Sexo</Label>
          <Select items={SEX_OPTIONS} value={sex || null} onValueChange={(v) => v && setSex(v)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Selecciona" />
            </SelectTrigger>
            <SelectContent>
              {SEX_OPTIONS.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="patient-height">Estatura (cm)</Label>
          <Input
            id="patient-height"
            type="number"
            min={50}
            max={250}
            step={0.1}
            value={height}
            onChange={(e) => setHeight(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="patient-phone">Teléfono</Label>
          <Input
            id="patient-phone"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(maskPhone(e.target.value))}
            placeholder="7000-1234"
            pattern="\d{4}-\d{4}"
            title="Ocho dígitos con guion (7000-1234)"
            inputMode="numeric"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="patient-email">Correo electrónico</Label>
          <Input
            id="patient-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            maxLength={254}
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="patient-address">Dirección de residencia</Label>
        <Input
          id="patient-address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          maxLength={200}
        />
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
