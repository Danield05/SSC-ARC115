import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDateTime, formatNumber, paddedDomain } from '../lib/format'
import type { Measurement } from '../types'

interface Props {
  items: Measurement[]
  /** Coeficiente de Pearson del resumen (todo el historial); null con menos de 10 mediciones. */
  r: number | null
  n: number
}

interface ScatterPoint {
  temp: number
  bpm: number
  iso: string
}

/** Dispersión temperatura contra pulso con su recta de regresión y el coeficiente r. */
export default function TempPulseScatter({ items, r, n }: Props) {
  const points: ScatterPoint[] = items.map((m) => ({ temp: m.temp_c, bpm: m.bpm, iso: m.ts }))
  const summary = `Dispersión de temperatura contra pulso: ${points.length} mediciones.${
    r === null ? ' Coeficiente r no disponible con menos de 10 mediciones.' : ` Coeficiente r = ${formatNumber(r, 2)}.`
  }`

  return (
    <Card>
      <CardHeader>
        <CardTitle>Temperatura contra pulso</CardTitle>
        <CardDescription>
          Cada punto es una medición; la línea es la recta de regresión del rango elegido.{' '}
          {r === null
            ? 'r: n/d con menos de 10 mediciones.'
            : `r = ${formatNumber(r, 2)} (historial completo, ${n} mediciones). La correlación no implica causalidad.`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {points.length === 0 ? (
          <div className="text-muted-foreground flex h-[240px] items-center justify-center text-sm">
            Sin mediciones en este rango
          </div>
        ) : (
          <div role="img" aria-label={summary}>
            <ResponsiveContainer width="100%" height={240}>
              <ScatterChart margin={{ top: 8, right: 12, bottom: 16, left: 0 }}>
                <CartesianGrid stroke="var(--border)" />
                <XAxis
                  dataKey="temp"
                  type="number"
                  name="Temperatura"
                  unit=" °C"
                  domain={paddedDomain(points.map((p) => p.temp))}
                  tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                  stroke="var(--border)"
                  label={{ value: 'Temperatura (°C)', position: 'insideBottom', offset: -8, fill: 'var(--muted-foreground)', fontSize: 11 }}
                />
                <YAxis
                  dataKey="bpm"
                  type="number"
                  name="Pulso"
                  unit=" lpm"
                  domain={paddedDomain(points.map((p) => p.bpm))}
                  tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={44}
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={(p) => {
                    const point = (p.payload as ReadonlyArray<{ payload?: ScatterPoint }> | undefined)?.[0]?.payload
                    if (!p.active || !point) return null
                    return (
                      <div className="bg-popover text-popover-foreground rounded-lg border px-3 py-2 text-xs shadow-md">
                        <p className="text-base font-semibold">
                          {formatNumber(point.temp, 1)} °C · {point.bpm} lpm
                        </p>
                        <p className="text-muted-foreground">{formatDateTime(point.iso)}</p>
                      </div>
                    )
                  }}
                />
                <Scatter
                  data={points}
                  fill="var(--chart-1)"
                  line={{ stroke: 'var(--chart-2)', strokeWidth: 2 }}
                  lineType="fitting"
                  isAnimationActive={false}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
