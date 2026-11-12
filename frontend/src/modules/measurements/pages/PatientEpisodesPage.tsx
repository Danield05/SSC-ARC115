import { Activity, BellRing, Clock, ShieldAlert } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import StatCard from '@/shared/components/StatCard'
import { usePatient } from '../../patients/hooks/usePatient'
import EpisodeCard from '../components/EpisodeCard'
import EpisodeTimeline from '../components/EpisodeTimeline'
import PatientHeader from '../components/PatientHeader'
import RangeFilter from '../components/RangeFilter'
import { useHistory } from '../hooks/useHistory'
import { findEpisodes, reviewOf } from '../lib/episodes'
import type { Measurement, RangeDays } from '../types'

const EMPTY: Measurement[] = []
const PAGE = 10

/** Episodios: las alertas seguidas agrupadas, en una línea de tiempo y en una lista. */
export default function PatientEpisodesPage() {
  const { code = '' } = useParams()
  const patient = usePatient(code)
  const [days, setDays] = useState<RangeDays>(90)
  const [shown, setShown] = useState(PAGE)
  const { data, error, notFound } = useHistory(code, days)
  const items = data?.items ?? EMPTY
  const episodes = useMemo(() => findEpisodes(items), [items])
  const stats = useMemo(
    () => ({
      alerts: episodes.reduce((sum, ep) => sum + ep.alerts.length, 0),
      pending: episodes.filter((ep) => reviewOf(ep).kind !== 'done').length,
    }),
    [episodes],
  )

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

  // De la más reciente a la más antigua; el número es el orden cronológico.
  const listed = episodes.map((ep, i) => ({ ep, number: i + 1 })).reverse()

  return (
    <>
      <PatientHeader code={code} patient={patient} intro="Episodios: las alertas seguidas, agrupadas, para ver cuánto duraron y si ya se revisaron. Es una forma de leer los datos, no un diagnóstico." />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <RangeFilter value={days} onChange={setDays} />
        {data && (
          <p className="text-muted-foreground text-sm">
            {items.length === 1 ? '1 medición' : `${items.length} mediciones`} en el rango
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

      {data && items.length > 0 && episodes.length === 0 && (
        <Alert>
          <AlertDescription>Ninguna medición de este rango superó los umbrales de alerta: no hay episodios.</AlertDescription>
        </Alert>
      )}

      {data && episodes.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard title="Episodios" value={String(episodes.length)} hint="Alertas seguidas, agrupadas" icon={Activity} />
            <StatCard
              title="Alertas incluidas"
              value={String(stats.alerts)}
              hint={`de ${items.length} mediciones`}
              icon={BellRing}
            />
            <StatCard
              title="Sin revisión completa"
              value={String(stats.pending)}
              hint="Episodios con alertas por revisar"
              icon={Clock}
            />
          </div>

          <EpisodeTimeline items={items} episodes={episodes} />

          <div className="flex flex-col gap-3">
            {listed.slice(0, shown).map(({ ep, number }) => (
              <EpisodeCard key={ep.start} number={number} episode={ep} thresholds={data.thresholds} code={code} />
            ))}
            {listed.length > shown && (
              <div className="flex justify-center">
                <Button variant="outline" size="sm" onClick={() => setShown((n) => n + PAGE)}>
                  Mostrar más ({listed.length - shown} restantes)
                </Button>
              </div>
            )}
          </div>
        </>
      )}
    </>
  )
}
