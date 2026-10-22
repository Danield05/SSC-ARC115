import { TriangleAlert } from 'lucide-react'
import { CartesianGrid, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { formatDateTime, formatNumber } from '../lib/format'
import type { Band } from '../lib/format'

export interface Point {
  /** Milisegundos desde 1970, para el eje de tiempo. */
  t: number
  iso: string
  value: number
  /** Fuera del rango de alerta de este parámetro. */
  outOfRange: boolean
}

interface Props {
  title: string
  unit: string
  decimals: number
  points: Point[]
  /** Franja de valores sin alerta; se sombrea de fondo. */
  band?: Band
  bandText?: string
  domain: [number, number]
  /** Conserva el dibujo anterior, atenuado, mientras llegan datos nuevos. */
  dimmed?: boolean
}

const DAY_MS = 24 * 60 * 60 * 1000
const MAX_DOTS = 150

interface TooltipProps {
  active?: boolean
  point?: Point
  title: string
  unit: string
  decimals: number
}

function ChartTooltip({ active, point, title, unit, decimals }: TooltipProps) {
  if (!active || !point) return null
  return (
    <div className="bg-popover text-popover-foreground rounded-lg border px-3 py-2 text-xs shadow-md">
      <p className="text-base font-semibold">
        {formatNumber(point.value, decimals)} {unit}
      </p>
      <p className="text-muted-foreground">{title}</p>
      <p className="text-muted-foreground">{formatDateTime(point.iso)}</p>
      {point.outOfRange && (
        <p className="text-destructive mt-1 flex items-center gap-1 font-medium">
          <TriangleAlert className="size-3" />
          Fuera de rango
        </p>
      )}
    </div>
  )
}

function tickFormatter(span: number) {
  return (t: number) =>
    new Date(t).toLocaleString(
      'es-SV',
      span <= 2 * DAY_MS ? { hour: 'numeric', minute: '2-digit' } : { day: 'numeric', month: 'short' },
    )
}

export default function MetricChart({ title, unit, decimals, points, band, bandText, domain, dimmed }: Props) {
  const latest = points.at(-1)
  const times = points.map((p) => p.t)
  let [tMin, tMax] = times.length ? [Math.min(...times), Math.max(...times)] : [0, 1]
  if (tMin === tMax) {
    // Un solo punto: se abre el eje medio día a cada lado para que se dibuje centrado.
    tMin -= DAY_MS / 2
    tMax += DAY_MS / 2
  }
  const showAllDots = points.length <= MAX_DOTS

  const renderDot = (props: { cx?: number; cy?: number; payload?: Point }) => {
    const { cx, cy, payload } = props
    const key = `dot-${payload?.t ?? 'x'}`
    if (cx === undefined || cy === undefined || !payload) return <g key={key} />
    if (!showAllDots && !payload.outOfRange) return <g key={key} />
    return (
      <circle
        key={key}
        cx={cx}
        cy={cy}
        r={payload.outOfRange ? 6 : 4}
        fill={payload.outOfRange ? 'var(--destructive)' : 'var(--chart-1)'}
        stroke="var(--card)"
        strokeWidth={2}
      />
    )
  }

  const summary = points.length
    ? `Gráfica de ${title.toLowerCase()}: ${points.length} mediciones, entre ${formatDateTime(points[0].iso)} y ${formatDateTime(points[points.length - 1].iso)}.`
    : `Gráfica de ${title.toLowerCase()} sin mediciones.`

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-3">
        <div className="space-y-1">
          <CardTitle>{title}</CardTitle>
          <CardDescription>{bandText ?? 'Sin umbral de alerta: solo seguimiento'}</CardDescription>
        </div>
        {latest && (
          <div className="text-right">
            <p className={cn('text-2xl font-semibold tracking-tight', latest.outOfRange && 'text-destructive')}>
              {formatNumber(latest.value, decimals)}
              <span className="text-muted-foreground ml-1 text-sm font-normal">{unit}</span>
            </p>
            <p className="text-muted-foreground text-xs">última medición</p>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {points.length === 0 ? (
          <div className="text-muted-foreground flex h-[220px] items-center justify-center text-sm">
            Sin mediciones en este rango
          </div>
        ) : (
          <div role="img" aria-label={summary} className={cn('transition-opacity', dimmed && 'opacity-60')}>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={points} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
                <CartesianGrid vertical={false} stroke="var(--border)" />
                {band && (
                  <ReferenceArea y1={band.from} y2={band.to} fill="var(--chart-1)" fillOpacity={0.1} stroke="none" />
                )}
                <XAxis
                  dataKey="t"
                  type="number"
                  scale="time"
                  domain={[tMin, tMax]}
                  tickFormatter={tickFormatter(tMax - tMin)}
                  tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                  stroke="var(--border)"
                  tickLine={false}
                  minTickGap={32}
                />
                <YAxis
                  domain={domain}
                  tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={40}
                  allowDecimals={false}
                />
                <Tooltip
                  cursor={{ stroke: 'var(--muted-foreground)', strokeWidth: 1 }}
                  content={(p) => (
                    <ChartTooltip
                      active={p.active}
                      point={(p.payload as ReadonlyArray<{ payload?: Point }> | undefined)?.[0]?.payload}
                      title={title}
                      unit={unit}
                      decimals={decimals}
                    />
                  )}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="var(--chart-1)"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  dot={renderDot}
                  activeDot={{ r: 6, fill: 'var(--chart-1)', stroke: 'var(--card)', strokeWidth: 2 }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
