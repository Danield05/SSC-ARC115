import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { REVIEW_LABEL } from '../lib/alerts'
import { markOf } from '../lib/episodes'
import type { Episode, EpisodeMark } from '../lib/episodes'
import { formatDate, formatDateTime } from '../lib/format'
import type { Measurement } from '../types'

const DAY_MS = 24 * 60 * 60 * 1000
/** Con más episodios que estos ya no se escribe el número sobre cada uno. */
const MAX_LABELS = 12

/** Forma y relleno de cada estado: el color nunca va solo. */
const MARK_CLASS: Record<EpisodeMark, string> = {
  pending: 'border-2 border-dashed border-destructive bg-destructive/10',
  confirmada: 'bg-destructive',
  falso_positivo: 'bg-muted-foreground/50',
  artefacto: 'border-2 border-muted-foreground bg-transparent',
}

const MARK_TEXT: Record<EpisodeMark, string> = {
  pending: 'Sin revisar',
  confirmada: REVIEW_LABEL.confirmada,
  falso_positivo: REVIEW_LABEL.falso_positivo,
  artefacto: REVIEW_LABEL.artefacto,
}

/**
 * Línea de tiempo anotada: las mediciones como marcas finas y cada episodio como una franja
 * sobre ellas, con el estado de su revisión. Es la vista de «anotaciones sobre una pista» de las
 * herramientas de PhysioNet, aplicada a nuestras alertas.
 */
export default function EpisodeTimeline({ items, episodes }: { items: Measurement[]; episodes: Episode[] }) {
  const times = items.map((m) => new Date(m.ts).getTime())
  const t0 = Math.min(...times)
  const t1 = Math.max(...times)
  const span = t1 > t0 ? t1 - t0 : DAY_MS
  const pct = (t: number) => ((t - t0) / span) * 100
  const labelled = episodes.length <= MAX_LABELS

  return (
    <Card>
      <CardHeader>
        <CardTitle>Línea de tiempo</CardTitle>
        <CardDescription>
          Las marcas grises son las mediciones; cada franja es un episodio de alertas, con el estado de su revisión. La escala es
          el tiempo real: los huecos son días sin mediciones.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="px-3">
          <div
            className="relative h-16"
            role="img"
            aria-label={`Línea de tiempo: ${items.length} mediciones y ${episodes.length} episodios entre ${formatDateTime(items[0].ts)} y ${formatDateTime(items[items.length - 1].ts)}.`}
          >
            <div className="bg-border absolute inset-x-0 top-8 h-px" aria-hidden />
            {times.map((t, i) => (
              <span
                key={items[i].record_id}
                className="bg-muted-foreground/40 absolute top-6 h-4 w-px"
                style={{ left: `${pct(t)}%` }}
                aria-hidden
              />
            ))}
            {episodes.map((ep, i) => {
              const a = new Date(ep.start).getTime()
              const b = new Date(ep.end).getTime()
              const mark = markOf(ep)
              const point = b === a
              return (
                <div
                  key={ep.start}
                  title={`Episodio ${i + 1} · ${formatDateTime(ep.start)}${point ? '' : ` a ${formatDateTime(ep.end)}`} · ${MARK_TEXT[mark]}`}
                  className={cn('absolute top-5 h-6 rounded-sm', MARK_CLASS[mark], point ? 'w-3 -translate-x-1/2' : 'min-w-3')}
                  style={{ left: `${pct(a)}%`, ...(point ? {} : { width: `${pct(b) - pct(a)}%` }) }}
                >
                  {labelled && (
                    <span className="text-foreground absolute -top-5 left-1/2 -translate-x-1/2 text-xs font-medium tabular-nums">
                      {i + 1}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
          <div className="text-muted-foreground mt-1 flex justify-between gap-2 text-xs">
            <span>{formatDate(items[0].ts)}</span>
            {t1 > t0 && <span>{formatDate(items[items.length - 1].ts)}</span>}
          </div>
        </div>

        <ul className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-xs" aria-label="Cómo leer la línea de tiempo">
          {(Object.keys(MARK_CLASS) as EpisodeMark[]).map((mark) => (
            <li key={mark} className="flex items-center gap-1.5">
              <span className={cn('h-3.5 w-5 rounded-sm', MARK_CLASS[mark])} aria-hidden />
              {MARK_TEXT[mark]}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
