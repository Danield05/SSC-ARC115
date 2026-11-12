import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import PageHeader from '@/shared/components/PageHeader'
import type { Patient } from '../../patients/types'
import PatientTabs from './PatientTabs'

interface Props {
  code: string
  patient: Patient | null
  /** Dato propio de la pestaña que se suma a «P-0002 · 24 años» (por ejemplo, la última medición). */
  extra?: string
  /** Qué muestra la pestaña; va debajo de las pestañas para que el título sea el mismo en todas. */
  intro?: string
}

/** Encabezado común de las pestañas del paciente: nombre, código y edad no cambian al pasar de una a otra. */
export default function PatientHeader({ code, patient, extra, intro }: Props) {
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
      <PageHeader title={patient?.name || `Paciente ${code}`} description={details} />
      <PatientTabs code={code} />
      {intro && <p className="text-muted-foreground text-sm">{intro}</p>}
    </>
  )
}
