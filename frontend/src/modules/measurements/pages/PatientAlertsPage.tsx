import { BellRing, CircleCheck, Percent, ShieldAlert, TriangleAlert } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import StatCard from '@/shared/components/StatCard'
import { useAuth } from '../../auth/hooks/useAuth'
import * as api from '../api/measurementsApi'
import AlertCard from '../components/AlertCard'
import PatientHeader from '../components/PatientHeader'
import RangeFilter from '../components/RangeFilter'
import { useHistory } from '../hooks/useHistory'
import { contextOf, countReviews } from '../lib/alerts'
import type { Measurement, RangeDays, Review, ReviewStatus } from '../types'

const EMPTY: Measurement[] = []
const PAGE = 10

type Filter = 'all' | 'pending'

/** Revisión de alertas: el equipo etiqueta cada una como confirmada, falso positivo o artefacto. */
export default function PatientAlertsPage() {
  const { code = '' } = useParams()
  const { user } = useAuth()
  const canReview = user?.role === 'admin' || user?.role === 'promoter'
  const [days, setDays] = useState<RangeDays>(90)
  const [filter, setFilter] = useState<Filter>('all')
  const [shown, setShown] = useState(PAGE)
  // Revisiones guardadas en esta sesión, por encima de lo que trajo el historial.
  const [saved, setSaved] = useState<Record<string, Review>>({})
  const { data, error, notFound } = useHistory(code, days)

  const items = useMemo(() => {
    const fetched = data?.items ?? EMPTY
    return fetched.map((m) => {
      const review = saved[`${code}|${m.ts}`]
      return review ? { ...m, review } : m
    })
  }, [data, saved, code])

  const alerts = useMemo(() => {
    if (!data) return []
    return items
      .flatMap((m, i) => (m.alert ? [{ m, context: contextOf(items, i, data.thresholds) }] : []))
      .reverse()
  }, [items, data])

  const counts = useMemo(() => countReviews(alerts.map((a) => a.m)), [alerts])
  const pending = counts.alerts - counts.reviewed
  const visible = filter === 'pending' ? alerts.filter((a) => !a.m.review) : alerts

  async function save(m: Measurement, status: ReviewStatus, note: string) {
    const review = await api.reviewAlert(code, m.ts, { status, note })
    setSaved((prev) => ({ ...prev, [`${code}|${m.ts}`]: review }))
  }

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

  const percent = (n: number) => (counts.reviewed ? `${Math.round((n / counts.reviewed) * 100)} %` : '—')

  return (
    <>
      <PatientHeader code={code} intro="Revisión de alertas: cada alerta se marca como confirmada, falso positivo o artefacto, con una nota opcional. Es un registro del equipo, no un diagnóstico." />

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

      {data && items.length > 0 && alerts.length === 0 && (
        <Alert>
          <AlertDescription>Ninguna medición de este rango superó los umbrales de alerta.</AlertDescription>
        </Alert>
      )}

      {alerts.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard title="Alertas" value={String(counts.alerts)} hint={`${pending} sin revisar`} icon={BellRing} />
            <StatCard
              title="Revisadas"
              value={String(counts.reviewed)}
              hint={`de ${counts.alerts} alertas`}
              icon={CircleCheck}
            />
            <StatCard
              title="Confirmadas"
              value={String(counts.confirmada)}
              hint={`${percent(counts.confirmada)} de las revisadas`}
              icon={TriangleAlert}
            />
            <StatCard
              title="Falsas alarmas"
              value={counts.falseAlarmPct === null ? '—' : `${counts.falseAlarmPct} %`}
              hint={`${counts.falsePositive} falso positivo · ${counts.artifact} artefacto`}
              icon={Percent}
            />
          </div>

          {!canReview && (
            <Alert>
              <AlertDescription>Tu rol es de solo lectura: puedes ver las revisiones, pero no crearlas.</AlertDescription>
            </Alert>
          )}

          <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar alertas">
            <Button
              size="sm"
              variant={filter === 'all' ? 'default' : 'outline'}
              aria-pressed={filter === 'all'}
              onClick={() => setFilter('all')}
            >
              Todas ({counts.alerts})
            </Button>
            <Button
              size="sm"
              variant={filter === 'pending' ? 'default' : 'outline'}
              aria-pressed={filter === 'pending'}
              onClick={() => setFilter('pending')}
            >
              Sin revisar ({pending})
            </Button>
          </div>

          {visible.length === 0 ? (
            <Alert>
              <AlertDescription>No quedan alertas sin revisar en este rango.</AlertDescription>
            </Alert>
          ) : (
            <div className="flex flex-col gap-3">
              {visible.slice(0, shown).map(({ m, context }) => (
                <AlertCard
                  key={m.record_id}
                  measurement={m}
                  thresholds={data!.thresholds}
                  context={context}
                  canReview={canReview}
                  onSave={(status, note) => save(m, status, note)}
                />
              ))}
              {visible.length > shown && (
                <div className="flex justify-center">
                  <Button variant="outline" size="sm" onClick={() => setShown((n) => n + PAGE)}>
                    Mostrar más ({visible.length - shown} restantes)
                  </Button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </>
  )
}
