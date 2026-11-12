import { ArrowLeft, ShieldAlert } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import PageHeader from '@/shared/components/PageHeader'
import { usePatient } from '../../patients/hooks/usePatient'
import DelayMap from '../components/DelayMap'
import DeviationStrip from '../components/DeviationStrip'
import PatientTabs from '../components/PatientTabs'
import RangeFilter from '../components/RangeFilter'
import SummaryPanel from '../components/SummaryPanel'
import TempPulseScatter from '../components/TempPulseScatter'
import { useHistory } from '../hooks/useHistory'
import { useSummary } from '../hooks/useSummary'
import type { RangeDays } from '../types'

/** Análisis del paciente: métricas del resumen, correlación temperatura–pulso y mapa de retardo. */
export default function PatientAnalysisPage() {
  const { code = '' } = useParams()
  const patient = usePatient(code)
  const [days, setDays] = useState<RangeDays>(90)
  const { data, error, notFound } = useHistory(code, days)
  const { data: summary } = useSummary(code)

  if (notFound) {
    return (
      <div className="flex flex-col items-center gap-2 py-16 text-center">
        <ShieldAlert className="text-muted-foreground size-10" />
        <h1 className="text-lg font-semibold">Paciente no encontrado</h1>
        <p className="text-muted-foreground text-sm">No existe o no tienes acceso a su historial.</p>
        <Link to="/patients" className="text-primary text-sm hover:underline">
          Volver a pacientes
        </Link>
      </div>
    )
  }

  const items = data?.items ?? []
  const title = patient?.name ? `${patient.name} · análisis` : `Paciente ${code} · análisis`

  return (
    <>
      <Link
        to="/patients"
        className="text-muted-foreground hover:text-foreground flex w-fit items-center gap-1 text-sm transition-colors"
      >
        <ArrowLeft className="size-4" />
        Pacientes
      </Link>
      <PageHeader
        title={title}
        description="Métricas y gráficas derivadas de las mediciones. Informativo: el sistema registra y da seguimiento, no diagnostica."
      />
      <PatientTabs code={code} />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {summary && <SummaryPanel summary={summary} />}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <RangeFilter value={days} onChange={setDays} />
        {data && (
          <p className="text-muted-foreground text-sm">
            {items.length === 1 ? '1 medición' : `${items.length} mediciones`} en el rango · filtra las gráficas de abajo
          </p>
        )}
      </div>

      {data && items.length === 0 && (
        <Alert>
          <AlertDescription>
            No hay mediciones en este rango.
            {days !== null && ' Prueba con un rango más amplio o con «Todo».'}
          </AlertDescription>
        </Alert>
      )}

      {items.length > 0 && <DeviationStrip items={items} />}

      {items.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-2">
          <TempPulseScatter
            items={items}
            r={summary?.correlation?.temp_bpm?.r ?? null}
            n={summary?.correlation?.temp_bpm?.n ?? 0}
          />
          <DelayMap items={items} />
        </div>
      )}
    </>
  )
}
