import { Line, LineChart, ReferenceDot, ResponsiveContainer, XAxis, YAxis } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatNumber, paddedDomain } from '../lib/format'

export interface SparkPoint {
  /** Milisegundos desde 1970. */
  t: number
  value: number
}

interface Props {
  title: string
  unit: string
  decimals: number
  points: SparkPoint[]
  /** Posición (índice) resaltada: la medición seleccionada en la línea de tiempo. */
  selected: number
}

/** Traza pequeña de una variable con la medición seleccionada resaltada. */
export default function Sparkline({ title, unit, decimals, points, selected }: Props) {
  const current = points[selected]
  const domain = paddedDomain(points.map((p) => p.value))
  const [tMin, tMax] = [points[0]?.t ?? 0, points.at(-1)?.t ?? 1]
  const summary = `Traza de ${title.toLowerCase()}: ${points.length} mediciones; seleccionada: ${
    current ? `${formatNumber(current.value, decimals)} ${unit}` : 'ninguna'
  }.`

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
        <CardDescription className="tabular-nums">
          {current ? `${formatNumber(current.value, decimals)} ${unit}` : '—'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div role="img" aria-label={summary}>
          <ResponsiveContainer width="100%" height={72}>
            <LineChart data={points} margin={{ top: 6, right: 8, bottom: 6, left: 8 }}>
              <XAxis dataKey="t" type="number" scale="time" domain={[tMin === tMax ? tMin - 1 : tMin, tMax]} hide />
              <YAxis domain={domain} hide />
              <Line
                type="monotone"
                dataKey="value"
                stroke="var(--chart-1)"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
              {current && (
                <ReferenceDot
                  x={current.t}
                  y={current.value}
                  r={5}
                  fill="var(--chart-1)"
                  stroke="var(--card)"
                  strokeWidth={2}
                  ifOverflow="extendDomain"
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
