import { useMemo, useState } from 'react'
import { CartesianGrid, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatNumber, paddedDomain } from '../lib/format'
import type { Measurement, Variable } from '../types'

/** Con menos mediciones el mapa no dice nada (mismo mínimo que la correlación). */
export const MIN_FOR_DELAY_MAP = 10

const VARIABLES: { key: Variable; label: string; unit: string }[] = [
  { key: 'bpm', label: 'Pulso', unit: 'lpm' },
  { key: 'temp_c', label: 'Temperatura', unit: '°C' },
  { key: 'spo2', label: 'SpO₂', unit: '%' },
  { key: 'weight_kg', label: 'Peso', unit: 'kg' },
]

interface Pair {
  x: number
  y: number
  from: string
  to: string
}

const shortDate = (iso: string) => new Date(iso).toLocaleDateString('es-SV', { day: 'numeric', month: 'short' })

/**
 * Mapa de retardo: cada punto compara una medición (eje X) con la siguiente (eje Y). Sobre la
 * diagonal el valor no cambió; lejos de ella cambió mucho entre dos visitas seguidas. Es la idea de
 * los mapas de Poincaré de PhysioNet aplicada a las mediciones del paciente, no a intervalos entre latidos.
 */
export default function DelayMap({ items }: { items: Measurement[] }) {
  const [variable, setVariable] = useState<Variable>('bpm')
  const meta = VARIABLES.find((v) => v.key === variable) ?? VARIABLES[0]
  const enough = items.length >= MIN_FOR_DELAY_MAP

  const map = useMemo(() => {
    if (items.length < MIN_FOR_DELAY_MAP) return null
    const pairs: Pair[] = []
    for (let i = 0; i < items.length - 1; i++) {
      pairs.push({ x: items[i][variable], y: items[i + 1][variable], from: items[i].ts, to: items[i + 1].ts })
    }
    const changes = pairs.map((p) => Math.abs(p.y - p.x))
    const biggest = changes.indexOf(Math.max(...changes))
    return {
      pairs,
      domain: paddedDomain(items.map((m) => m[variable])),
      meanChange: changes.reduce((sum, c) => sum + c, 0) / changes.length,
      biggestChange: changes[biggest],
      biggestPair: pairs[biggest],
    }
  }, [items, variable])

  return (
    <Card>
      <CardHeader className="gap-3">
        <div className="space-y-1.5">
          <CardTitle>Mapa de retardo</CardTitle>
          <CardDescription>
            Cada punto compara una medición con la siguiente. Sobre la línea punteada el valor no cambió; lejos de ella,
            cambió mucho de una visita a la siguiente. Informativo: no es un diagnóstico.
          </CardDescription>
        </div>
        <div role="group" aria-label="Variable del mapa de retardo" className="flex flex-wrap gap-2">
          {VARIABLES.map((v) => (
            <Button
              key={v.key}
              size="sm"
              variant={v.key === variable ? 'default' : 'outline'}
              aria-pressed={v.key === variable}
              onClick={() => setVariable(v.key)}
            >
              {v.label}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {!enough || !map ? (
          <div className="text-muted-foreground flex h-[240px] items-center justify-center text-center text-sm">
            n/d: se necesitan al menos {MIN_FOR_DELAY_MAP} mediciones en el rango (hay {items.length}).
          </div>
        ) : (
          <>
            <div
              role="img"
              aria-label={`Mapa de retardo de ${meta.label.toLowerCase()}: ${map.pairs.length} pares de mediciones consecutivas. Cambio promedio ${formatNumber(map.meanChange, 1)} ${meta.unit}.`}
            >
              <ResponsiveContainer width="100%" height={260}>
                <ScatterChart margin={{ top: 8, right: 12, bottom: 20, left: 8 }}>
                  <CartesianGrid stroke="var(--border)" />
                  <XAxis
                    dataKey="x"
                    type="number"
                    name="Medición"
                    domain={map.domain}
                    tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                    stroke="var(--border)"
                    label={{ value: `Medición (${meta.unit})`, position: 'insideBottom', offset: -10, fill: 'var(--muted-foreground)', fontSize: 11 }}
                  />
                  <YAxis
                    dataKey="y"
                    type="number"
                    name="Siguiente medición"
                    domain={map.domain}
                    tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={52}
                    label={{ value: `Siguiente (${meta.unit})`, angle: -90, position: 'insideLeft', offset: 4, fill: 'var(--muted-foreground)', fontSize: 11 }}
                  />
                  <ReferenceLine
                    segment={[
                      { x: map.domain[0], y: map.domain[0] },
                      { x: map.domain[1], y: map.domain[1] },
                    ]}
                    stroke="var(--muted-foreground)"
                    strokeDasharray="4 4"
                  />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    content={(p) => {
                      const pair = (p.payload as ReadonlyArray<{ payload?: Pair }> | undefined)?.[0]?.payload
                      if (!p.active || !pair) return null
                      return (
                        <div className="bg-popover text-popover-foreground rounded-lg border px-3 py-2 text-xs shadow-md">
                          <p className="text-base font-semibold">
                            {formatNumber(pair.x, 1)} → {formatNumber(pair.y, 1)} {meta.unit}
                          </p>
                          <p className="text-muted-foreground">
                            {shortDate(pair.from)} → {shortDate(pair.to)}
                          </p>
                        </div>
                      )
                    }}
                  />
                  <Scatter data={map.pairs} fill="var(--chart-1)" isAnimationActive={false} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <p className="text-muted-foreground text-sm">
              Cambio promedio entre mediciones consecutivas: {formatNumber(map.meanChange, 1)} {meta.unit}. Mayor salto:{' '}
              {formatNumber(map.biggestChange, 1)} {meta.unit} ({shortDate(map.biggestPair.from)} →{' '}
              {shortDate(map.biggestPair.to)}).
            </p>
            {variable === 'bpm' && (
              <p className="text-muted-foreground text-xs">
                El pulso es el promedio de cada visita: el mapa muestra su estabilidad entre visitas, no el ritmo del
                corazón.
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
