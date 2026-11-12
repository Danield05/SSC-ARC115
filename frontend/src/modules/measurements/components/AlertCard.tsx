import { Pencil } from 'lucide-react'
import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { NOTE_MAX, REVIEW_BADGE, REVIEW_HELP, REVIEW_LABEL, REVIEW_STATUSES, reasons } from '../lib/alerts'
import type { Context } from '../lib/alerts'
import { formatDateTime, formatNumber, spo2OutOfRange, tempOutOfRange } from '../lib/format'
import type { Measurement, Review, ReviewStatus, Thresholds } from '../types'

interface Props {
  measurement: Measurement
  thresholds: Thresholds
  context: Context
  /** Admin y promotor etiquetan; el evaluador (viewer) solo lee. */
  canReview: boolean
  onSave: (status: ReviewStatus, note: string) => Promise<void>
}

function Value({ label, value, out }: { label: string; value: string; out?: boolean }) {
  return (
    <div>
      <dt className="text-muted-foreground text-xs">{label}</dt>
      <dd className={cn('text-sm font-medium tabular-nums', out && 'text-destructive font-semibold')}>
        {value}
        {out && <span className="sr-only"> (fuera de rango)</span>}
      </dd>
    </div>
  )
}

function Neighbor({ label, m }: { label: string; m: Measurement | null }) {
  return (
    <p>
      <span className="font-medium">{label}:</span>{' '}
      {m
        ? `${formatDateTime(m.ts)} · ${formatNumber(m.temp_c, 1)} °C · SpO₂ ${m.spo2} % · ${m.bpm} lpm`
        : 'no hay otra en este rango'}
    </p>
  )
}

/** Una alerta con sus valores, su contexto y los controles para etiquetarla. */
export default function AlertCard({ measurement: m, thresholds, context, canReview, onSave }: Props) {
  const why = reasons(m, thresholds)
  const review: Review | null = m.review
  const [editing, setEditing] = useState(false)
  const [status, setStatus] = useState<ReviewStatus | null>(review?.status ?? null)
  const [note, setNote] = useState(review?.note ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const showForm = canReview && (!review || editing)

  async function save() {
    if (!status) return
    setBusy(true)
    setError('')
    try {
      await onSave(status, note)
      setEditing(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo guardar la revisión.')
    } finally {
      setBusy(false)
    }
  }

  function startEditing() {
    setStatus(review?.status ?? null)
    setNote(review?.note ?? '')
    setError('')
    setEditing(true)
  }

  return (
    <Card>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="font-medium">{formatDateTime(m.ts)}</p>
            <p className="text-muted-foreground text-sm">
              {why.length ? why.join(' · ') : 'Marcada como alerta por el dispositivo'}
            </p>
          </div>
          {review ? (
            <Badge variant={REVIEW_BADGE[review.status]}>{REVIEW_LABEL[review.status]}</Badge>
          ) : (
            <Badge variant="outline">Pendiente de revisión</Badge>
          )}
        </div>

        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Value label="Temperatura" value={`${formatNumber(m.temp_c, 1)} °C`} out={tempOutOfRange(m.temp_c, thresholds)} />
          <Value label="SpO₂" value={`${m.spo2} %`} out={spo2OutOfRange(m.spo2, thresholds)} />
          <Value label="Pulso" value={`${m.bpm} lpm`} />
          <Value label="Peso" value={`${formatNumber(m.weight_kg, 1)} kg`} />
        </dl>

        <div className="text-muted-foreground flex flex-col gap-0.5 text-xs">
          <Neighbor label="Anterior" m={context.before} />
          <Neighbor label="Siguiente" m={context.after} />
          {context.isolated && (
            <p className="text-foreground pt-1">
              <Badge variant="secondary">Lectura aislada</Badge> La anterior y la siguiente están en rango.
            </p>
          )}
        </div>

        {review && !showForm && (
          <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-3 text-sm">
            <div className="min-w-0">
              {review.note && <p className="break-words">«{review.note}»</p>}
              <p className="text-muted-foreground text-xs">
                Revisó {review.reviewed_by} · {formatDateTime(review.reviewed_at)}
              </p>
            </div>
            {canReview && (
              <Button variant="outline" size="sm" onClick={startEditing}>
                <Pencil />
                Cambiar
              </Button>
            )}
          </div>
        )}

        {showForm && (
          <form
            className="flex flex-col gap-3 border-t pt-3"
            onSubmit={(e) => {
              e.preventDefault()
              void save()
            }}
          >
            <fieldset className="flex flex-col gap-2">
              <legend className="mb-1 text-sm font-medium">¿Qué fue esta alerta?</legend>
              <div className="flex flex-wrap gap-2">
                {REVIEW_STATUSES.map((s) => (
                  <Button
                    key={s}
                    type="button"
                    size="sm"
                    variant={status === s ? 'default' : 'outline'}
                    aria-pressed={status === s}
                    onClick={() => setStatus(s)}
                  >
                    {REVIEW_LABEL[s]}
                  </Button>
                ))}
              </div>
              <p className="text-muted-foreground min-h-4 text-xs">{status ? REVIEW_HELP[status] : 'Elige una etiqueta.'}</p>
            </fieldset>
            <div className="flex flex-col gap-1">
              <label htmlFor={`note-${m.record_id}`} className="text-sm font-medium">
                Nota <span className="text-muted-foreground font-normal">(opcional)</span>
              </label>
              <Input
                id={`note-${m.record_id}`}
                value={note}
                maxLength={NOTE_MAX}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Por ejemplo: el sensor se movió durante la lectura"
              />
              <p className="text-muted-foreground text-right text-xs tabular-nums">
                {note.length}/{NOTE_MAX}
              </p>
            </div>
            {error && (
              <p role="alert" className="text-destructive text-sm">
                {error}
              </p>
            )}
            <div className="flex gap-2">
              <Button type="submit" size="sm" disabled={!status || busy}>
                {busy ? 'Guardando…' : 'Guardar revisión'}
              </Button>
              {review && (
                <Button type="button" variant="ghost" size="sm" disabled={busy} onClick={() => setEditing(false)}>
                  Cancelar
                </Button>
              )}
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  )
}
