import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { REVIEW_BADGE, REVIEW_LABEL } from '../lib/alerts'
import { extremes, reviewOf, spanText } from '../lib/episodes'
import type { Episode } from '../lib/episodes'
import { formatDateTime } from '../lib/format'
import type { Thresholds } from '../types'

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-muted-foreground text-xs">{label}</dt>
      <dd className="text-sm font-medium">{children}</dd>
    </div>
  )
}

/** Un episodio: cuándo empezó y terminó, qué tan lejos llegó, si volvió a rango y su revisión. */
export default function EpisodeCard({
  number,
  episode: ep,
  thresholds,
  code,
}: {
  number: number
  episode: Episode
  thresholds: Thresholds
  code: string
}) {
  const review = reviewOf(ep)
  const peaks = extremes(ep, thresholds)
  const single = ep.start === ep.end
  return (
    <Card>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="font-medium">
              Episodio {number} · {formatDateTime(ep.start)}
              {!single && ` → ${formatDateTime(ep.end)}`}
            </p>
            <p className="text-muted-foreground text-sm">{peaks.join(' · ')}</p>
          </div>
          <div className="flex flex-wrap gap-1">
            {review.kind === 'pending' && <Badge variant="outline">Sin revisar</Badge>}
            {review.kind === 'partial' && (
              <Badge variant="outline">
                {review.reviewed} de {review.total} revisadas
              </Badge>
            )}
            {review.kind === 'done' &&
              review.statuses.map((s) => (
                <Badge key={s} variant={REVIEW_BADGE[s]}>
                  {REVIEW_LABEL[s]}
                </Badge>
              ))}
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Fact label="Alertas">{ep.alerts.length === 1 ? '1 medición' : `${ep.alerts.length} mediciones`}</Fact>
          <Fact label="Duración">{spanText(ep)}</Fact>
          <Fact label="Volvió a rango">
            {ep.recovery ? formatDateTime(ep.recovery.ts) : 'Sin medición posterior'}
          </Fact>
          <Fact label="Revisión">
            <Link to={`/patients/${encodeURIComponent(code)}/alertas`} className="text-primary hover:underline">
              Ver en Alertas
            </Link>
          </Fact>
        </dl>
      </CardContent>
    </Card>
  )
}
