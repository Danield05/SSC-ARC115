import { Activity, ChevronLeft, ChevronRight, HeartPulse, Pause, Play, Scale, ShieldAlert, Thermometer, TriangleAlert } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import DeviationMark from '../components/DeviationMark'
import PatientHeader from '../components/PatientHeader'
import RangeFilter from '../components/RangeFilter'
import Sparkline from '../components/Sparkline'
import { useHistory } from '../hooks/useHistory'
import { deviationClass, deviationLabel, deviationsOf } from '../lib/deviation'
import type { Deviation } from '../lib/deviation'
import { formatDateTime, formatNumber, spo2OutOfRange, tempOutOfRange } from '../lib/format'
import type { RangeDays, Variable } from '../types'

const PLAY_MS = 800

interface BigValueProps {
  title: string
  icon: LucideIcon
  value: string
  unit: string
  deviation: Deviation | null
  outOfRange?: boolean
}

/** Valor grande de la medición seleccionada. El estado se dice con texto e icono, no solo color. */
function BigValue({ title, icon: Icon, value, unit, deviation, outOfRange }: BigValueProps) {
  const note = outOfRange ? 'Fuera de rango' : deviationLabel(deviation)
  return (
    <Card className={cn(deviationClass(deviation))}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardDescription className="text-current">{title}</CardDescription>
        <Icon className="size-5" aria-hidden />
      </CardHeader>
      <CardContent>
        <p className={cn('text-5xl font-semibold tracking-tight tabular-nums', outOfRange && 'text-destructive')}>
          {value}
          <span className="ml-1 text-xl font-normal opacity-80">{unit}</span>
          <DeviationMark deviation={deviation} className="ml-2 align-middle" />
        </p>
        <p className="mt-1 flex min-h-5 items-center gap-1 text-sm">
          {outOfRange && <TriangleAlert className="text-destructive size-4" aria-hidden />}
          {note}
        </p>
      </CardContent>
    </Card>
  )
}

export default function PatientMonitorPage() {
  const { code = '' } = useParams()
  const [days, setDays] = useState<RangeDays>(30)
  const { data, loading, error, notFound } = useHistory(code, days)
  // null = la última medición; así el deslizador no se queda atrás cuando llegan datos nuevos.
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [playing, setPlaying] = useState(false)

  const items = useMemo(() => data?.items ?? [], [data])
  const last = items.length - 1
  const index = items.length === 0 ? 0 : Math.min(selectedIndex ?? last, last)

  const deviations = useMemo(() => {
    const variables: Variable[] = ['temp_c', 'spo2', 'bpm', 'weight_kg']
    return Object.fromEntries(variables.map((v) => [v, deviationsOf(items, v)])) as Record<Variable, (Deviation | null)[]>
  }, [items])

  const series = useMemo(() => {
    const pick = (variable: Variable) => items.map((m) => ({ t: new Date(m.ts).getTime(), value: m[variable] }))
    return { temp_c: pick('temp_c'), spo2: pick('spo2'), bpm: pick('bpm'), weight_kg: pick('weight_kg') }
  }, [items])

  // Reproducir: avanza una medición cada PLAY_MS y se detiene sola al llegar a la última.
  const isPlaying = playing && index < last
  useEffect(() => {
    if (!isPlaying) return
    const timer = setInterval(() => setSelectedIndex((current) => Math.min((current ?? last) + 1, last)), PLAY_MS)
    return () => clearInterval(timer)
  }, [isPlaying, last])

  function changeRange(value: RangeDays) {
    setDays(value)
    setSelectedIndex(null)
    setPlaying(false)
  }

  function select(next: number) {
    setPlaying(false)
    setSelectedIndex(Math.max(0, Math.min(next, last)))
  }

  function togglePlay() {
    if (isPlaying) return setPlaying(false)
    // Si ya está en la última, vuelve al inicio para recorrer todo.
    if (index >= last) setSelectedIndex(0)
    setPlaying(true)
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

  const current = items[index]
  const thresholds = data?.thresholds
  const alertCount = items.filter((m) => m.alert).length

  return (
    <>
      <PatientHeader code={code} intro="Recorre las mediciones con la línea de tiempo. Informativo: el sistema registra y da seguimiento, no diagnostica." />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <RangeFilter value={days} onChange={changeRange} />
        {data && (
          <p className="text-muted-foreground text-sm">
            {items.length === 1 ? '1 medición' : `${items.length} mediciones`}
            {alertCount > 0 && ` · ${alertCount} con alerta`}
          </p>
        )}
      </div>

      {data && items.length === 0 && !loading && (
        <Alert>
          <AlertDescription>
            No hay mediciones en este rango.
            {days !== null && ' Prueba con un rango más amplio o con «Todo».'}
          </AlertDescription>
        </Alert>
      )}

      {current && thresholds && (
        <>
          <Card>
            <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 space-y-0">
              <div className="space-y-1">
                <CardTitle>{formatDateTime(current.ts)}</CardTitle>
                <CardDescription>
                  Medición {index + 1} de {items.length} · {current.device_id}
                </CardDescription>
              </div>
              {current.alert ? (
                <Badge variant="destructive">
                  <TriangleAlert />
                  Alerta
                </Badge>
              ) : (
                <Badge variant="outline">Normal</Badge>
              )}
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2">
                <Button size="icon" variant="outline" aria-label="Medición anterior" disabled={index <= 0} onClick={() => select(index - 1)}>
                  <ChevronLeft />
                </Button>
                <Button
                  size="icon"
                  variant="outline"
                  aria-label={isPlaying ? 'Pausar' : 'Reproducir'}
                  disabled={items.length < 2}
                  onClick={togglePlay}
                >
                  {isPlaying ? <Pause /> : <Play />}
                </Button>
                <Button size="icon" variant="outline" aria-label="Medición siguiente" disabled={index >= last} onClick={() => select(index + 1)}>
                  <ChevronRight />
                </Button>
                <div className="relative flex-1">
                  {/* Marcas de las mediciones con alerta sobre la pista. */}
                  <div className="pointer-events-none absolute inset-x-2 top-0 h-2" aria-hidden>
                    {items.map(
                      (m, i) =>
                        m.alert && (
                          <span
                            key={m.record_id}
                            className="bg-destructive absolute top-0 h-2 w-1 -translate-x-1/2 rounded-full"
                            style={{ left: `${last === 0 ? 50 : (i / last) * 100}%` }}
                          />
                        ),
                    )}
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={Math.max(last, 0)}
                    step={1}
                    value={index}
                    onChange={(e) => select(Number(e.target.value))}
                    aria-label="Línea de tiempo de las mediciones"
                    aria-valuetext={`${formatDateTime(current.ts)}${current.alert ? ', con alerta' : ''}`}
                    className="accent-primary mt-3 h-2 w-full cursor-pointer"
                  />
                </div>
              </div>
              {alertCount > 0 && (
                <p className="text-muted-foreground text-xs">
                  Las marcas rojas sobre la pista señalan las {alertCount} mediciones con alerta. Con el teclado: flechas izquierda y
                  derecha, Inicio y Fin.
                </p>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <BigValue
              title="Temperatura"
              icon={Thermometer}
              value={formatNumber(current.temp_c, 1)}
              unit="°C"
              deviation={deviations.temp_c[index]}
              outOfRange={tempOutOfRange(current.temp_c, thresholds)}
            />
            <BigValue
              title="Oxigenación (SpO₂)"
              icon={Activity}
              value={String(current.spo2)}
              unit="%"
              deviation={deviations.spo2[index]}
              outOfRange={spo2OutOfRange(current.spo2, thresholds)}
            />
            <BigValue title="Pulso" icon={HeartPulse} value={String(current.bpm)} unit="lpm" deviation={deviations.bpm[index]} />
            <BigValue
              title="Peso"
              icon={Scale}
              value={formatNumber(current.weight_kg, 1)}
              unit="kg"
              deviation={deviations.weight_kg[index]}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Sparkline title="Temperatura" unit="°C" decimals={1} points={series.temp_c} selected={index} />
            <Sparkline title="SpO₂" unit="%" decimals={0} points={series.spo2} selected={index} />
            <Sparkline title="Pulso" unit="lpm" decimals={0} points={series.bpm} selected={index} />
            <Sparkline title="Peso" unit="kg" decimals={1} points={series.weight_kg} selected={index} />
          </div>

          <p className="text-muted-foreground text-xs">
            El fondo y la flecha de cada valor indican cuánto se aleja de las 10 mediciones anteriores de esta persona (a partir de la
            cuarta medición): ámbar, algo; rojo, mucho. No es un umbral clínico.
          </p>
        </>
      )}
    </>
  )
}
