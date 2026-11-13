import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Skeleton } from '@/components/ui/skeleton'
import { usePatient } from '../../patients/hooks/usePatient'
import MeasureButton from './MeasureButton'
import PatientTabs from './PatientTabs'

interface Props {
  code: string
  /** Dato propio de la pestaña que se suma a «P-0002 · 24 años» (por ejemplo, la última medición). */
  extra?: string
  /** Qué muestra la pestaña; va debajo de las pestañas para que el título sea el mismo en todas. */
  intro?: string
}

/**
 * Encabezado común de las pestañas del paciente: el título es solo el nombre y el código y la edad
 * van debajo. Mientras llega el nombre se reserva su lugar, sin mostrar el código como título.
 */
export default function PatientHeader({ code, extra, intro }: Props) {
  const { patient, loading } = usePatient(code)
  const details = [code, patient?.age != null ? `${patient.age} años` : '', extra].filter(Boolean).join(' · ')
  return (
    <>
      <Link
        to="/patients"
        className="text-muted-foreground hover:text-foreground flex w-fit items-center gap-1 text-sm transition-colors"
      >
        <ArrowLeft className="size-4" />
        Pacientes
      </Link>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          {loading ? (
            <Skeleton className="h-8 w-64 max-w-full" aria-label="Cargando paciente" />
          ) : (
            <h1 className="text-2xl font-semibold tracking-tight">{patient?.name || 'Paciente'}</h1>
          )}
          <p className="text-muted-foreground text-sm">{details}</p>
        </div>
        <MeasureButton code={code} />
      </div>
      <PatientTabs code={code} />
      {intro && <p className="text-muted-foreground text-sm">{intro}</p>}
    </>
  )
}
