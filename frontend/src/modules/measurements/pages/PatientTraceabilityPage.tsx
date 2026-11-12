import { Clock, Database, ShieldAlert, Wifi, WifiOff } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import StatCard from '@/shared/components/StatCard'
import PatientHeader from '../components/PatientHeader'
import RangeFilter from '../components/RangeFilter'
import TraceabilityTable from '../components/TraceabilityTable'
import { useHistory } from '../hooks/useHistory'
import { delayMs, formatDelay, syncState } from '../lib/traceability'
import type { Measurement, RangeDays } from '../types'

const EMPTY: Measurement[] = []

/** Trazabilidad y sincronización: cuándo se midió cada valor y cuándo llegó a la nube. */
export default function PatientTraceabilityPage() {
  const { code = '' } = useParams()
  const [days, setDays] = useState<RangeDays>(30)
  const { data, error, notFound } = useHistory(code, days)
  const items = data?.items ?? EMPTY

  const stats = useMemo(() => {
    const known = items.filter((m) => syncState(m) !== 'unknown')
    const onTime = known.filter((m) => syncState(m) === 'on_time').length
    const delays = known.map((m) => delayMs(m) ?? 0)
    return {
      known: known.length,
      onTime,
      offline: known.length - onTime,
      maxDelay: delays.length ? Math.max(...delays) : null,
    }
  }, [items])

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

  const percent = (n: number) => (stats.known ? `${Math.round((n / stats.known) * 100)} %` : '—')

  return (
    <>
      <PatientHeader code={code} intro="Trazabilidad y sincronización: cuándo se midió cada valor y cuándo llegó a la nube. Muestra que el dispositivo guarda sin conexión y envía después." />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <RangeFilter value={days} onChange={setDays} />
        {data && (
          <p className="text-muted-foreground text-sm">
            {items.length === 1 ? '1 medición' : `${items.length} mediciones`}
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

      {items.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard title="Mediciones" value={String(items.length)} hint="En el rango elegido" icon={Database} />
            <StatCard
              title="Enviadas al momento"
              value={percent(stats.onTime)}
              hint={`${stats.onTime} de ${stats.known}`}
              icon={Wifi}
            />
            <StatCard
              title="Guardadas sin conexión"
              value={String(stats.offline)}
              hint={`${percent(stats.offline)} · enviadas después`}
              icon={WifiOff}
            />
            <StatCard
              title="Mayor retraso"
              value={stats.maxDelay === null ? '—' : formatDelay(stats.maxDelay)}
              hint="Entre medir y llegar a la nube"
              icon={Clock}
            />
          </div>
          <TraceabilityTable items={items} />
        </>
      )}
    </>
  )
}
