import { ArrowDown, ArrowRight, ArrowUp, BarChart3, Percent, Ruler, Scale, Sigma } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import StatCard from '@/shared/components/StatCard'
import { formatNumber } from '../lib/format'
import type { Summary, Trend, Variable } from '../types'

const WINDOWS = ['7', '30', '90'] as const

const VARIABLES: { key: Variable; label: string; unit: string; decimals: number }[] = [
  { key: 'weight_kg', label: 'Peso', unit: 'kg', decimals: 1 },
  { key: 'temp_c', label: 'Temperatura', unit: '°C', decimals: 1 },
  { key: 'spo2', label: 'SpO₂', unit: '%', decimals: 1 },
  { key: 'bpm', label: 'Pulso', unit: 'lpm', decimals: 0 },
]

const signed = (value: number, decimals: number) => `${value > 0 ? '+' : ''}${formatNumber(value, decimals)}`

/** Intensidad de la correlación según |r| (cortes de 0,3 y 0,6). */
function correlationText(r: number) {
  const abs = Math.abs(r)
  const strength = abs < 0.3 ? 'débil' : abs < 0.6 ? 'moderada' : 'fuerte'
  return `Correlación ${strength} ${r >= 0 ? 'positiva' : 'negativa'}`
}

/** La tendencia lleva flecha y texto, no solo color. */
function TrendCell({
  trend,
  unit,
  decimals,
  compact,
}: {
  trend: Trend | null
  unit: string
  decimals: number
  /** Sin el detalle por día: para la línea bajo el nombre en pantallas angostas. */
  compact?: boolean
}) {
  if (!trend) return <span className="text-muted-foreground">n/d</span>
  const Icon = trend.label === 'sube' ? ArrowUp : trend.label === 'baja' ? ArrowDown : ArrowRight
  return (
    <span className="inline-flex items-center gap-1">
      <Icon className="size-4" aria-hidden />
      {trend.label}
      {!compact && (
        <span className="text-muted-foreground text-xs">
          ({signed(trend.per_day, decimals + 1)} {unit}/día)
        </span>
      )}
    </span>
  )
}

export default function SummaryPanel({ summary }: { summary: Summary }) {
  const [win, setWin] = useState<(typeof WINDOWS)[number]>('30')
  const { windows, trend } = summary

  if (summary.count === 0 || !windows || !trend) return null

  const change = summary.weight_change
  const corr = summary.correlation?.temp_bpm
  const current = windows[win]

  return (
    <section aria-label="Resumen del paciente" className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="IMC"
          value={summary.bmi ? formatNumber(summary.bmi.value, 1) : '—'}
          hint={summary.bmi ? (summary.bmi.category ?? 'Sin categoría para esta edad') : 'Falta la estatura en la ficha'}
          icon={Ruler}
        />
        <StatCard
          title="Variación de peso"
          value={change?.vs_first_kg == null ? '—' : `${signed(change.vs_first_kg, 1)} kg`}
          hint={
            change?.vs_first_kg == null
              ? 'Se necesitan al menos 2 mediciones'
              : `${signed(change.vs_first_pct ?? 0, 1)} % desde la primera · ${signed(change.vs_previous_kg ?? 0, 1)} kg vs la anterior`
          }
          icon={Scale}
        />
        <StatCard
          title="Mediciones con alerta"
          value={summary.alert_pct == null ? '—' : `${formatNumber(summary.alert_pct, 1)} %`}
          hint={`${summary.count} ${summary.count === 1 ? 'medición' : 'mediciones'} en total`}
          icon={Percent}
        />
        <StatCard
          title="Temperatura y pulso"
          value={corr ? `r = ${formatNumber(corr.r, 2)}` : 'n/d'}
          hint={corr ? correlationText(corr.r) : 'n/d con menos de 10 mediciones'}
          icon={Sigma}
        />
      </div>

      <Card>
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 space-y-0">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="size-4" aria-hidden />
              Promedios, mínimos y máximos
            </CardTitle>
            <CardDescription>
              Ventana hasta la última medición ({current.n} {current.n === 1 ? 'medición' : 'mediciones'}). La
              tendencia usa todo el historial.
            </CardDescription>
          </div>
          <div role="group" aria-label="Ventana de tiempo" className="flex gap-2">
            {WINDOWS.map((w) => (
              <Button
                key={w}
                size="sm"
                variant={w === win ? 'default' : 'outline'}
                aria-pressed={w === win}
                onClick={() => setWin(w)}
              >
                {w} días
              </Button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Parámetro</TableHead>
                <TableHead className="text-right">Promedio</TableHead>
                <TableHead className="text-right">Mínimo</TableHead>
                <TableHead className="text-right">Máximo</TableHead>
                <TableHead className="hidden sm:table-cell">Tendencia</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {VARIABLES.map((v) => {
                const s = current[v.key]
                return (
                  <TableRow key={v.key}>
                    <TableCell className="font-medium">
                      {v.label}
                      {/* En pantallas angostas la tendencia no cabe como columna: va bajo el nombre. */}
                      <div className="mt-0.5 text-xs font-normal sm:hidden">
                        <TrendCell trend={trend[v.key]} unit={v.unit} decimals={v.decimals} compact />
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{s ? `${formatNumber(s.avg, v.decimals)} ${v.unit}` : '—'}</TableCell>
                    <TableCell className="text-right">{s ? formatNumber(s.min, v.decimals) : '—'}</TableCell>
                    <TableCell className="text-right">{s ? formatNumber(s.max, v.decimals) : '—'}</TableCell>
                    <TableCell className="hidden sm:table-cell">
                      <TrendCell trend={trend[v.key]} unit={v.unit} decimals={v.decimals} />
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <p className="text-muted-foreground text-xs">
        La correlación no implica causalidad. Este sistema registra y da seguimiento; no emite diagnósticos médicos.
      </p>
    </section>
  )
}
