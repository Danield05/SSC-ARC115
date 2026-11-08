import { Activity, ArrowLeft, Download, FileSpreadsheet, MonitorPlay, ShieldAlert, Thermometer, HeartPulse, Scale } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import PageHeader from '@/shared/components/PageHeader'
import StatCard from '@/shared/components/StatCard'
import VitalInfoDialog from '@/shared/components/VitalInfoDialog'
import type { VitalKey } from '@/shared/vitals/vitalInfo'
import { usePatient } from '../../patients/hooks/usePatient'
import MeasurementsTable from '../components/MeasurementsTable'
import MetricChart from '../components/MetricChart'
import SummaryPanel from '../components/SummaryPanel'
import TempPulseScatter from '../components/TempPulseScatter'
import type { Point } from '../components/MetricChart'
import RangeFilter from '../components/RangeFilter'
import { useExport } from '../hooks/useExport'
import { useHistory } from '../hooks/useHistory'
import { useSummary } from '../hooks/useSummary'
import { formatDateTime, formatNumber, paddedDomain, spo2OutOfRange, tempOutOfRange } from '../lib/format'
import type { Measurement, RangeDays } from '../types'

function toPoints(items: Measurement[], pick: (m: Measurement) => number, out?: (v: number) => boolean): Point[] {
  return items.map((m) => {
    const value = pick(m)
    return { t: new Date(m.ts).getTime(), iso: m.ts, value, outOfRange: out ? out(value) : false }
  })
}

export default function PatientHistoryPage() {
  const { code = '' } = useParams()
  const patient = usePatient(code)
  const [days, setDays] = useState<RangeDays>(30)
  const { data, loading, error, notFound } = useHistory(code, days)
  const { data: summary } = useSummary(code)
  const exporter = useExport(code, days)
  const [infoVital, setInfoVital] = useState<VitalKey>('weight')
  const [infoOpen, setInfoOpen] = useState(false)

  function showInfo(key: VitalKey) {
    setInfoVital(key)
    setInfoOpen(true)
  }

  const charts = useMemo(() => {
    if (!data) return null
    const { items, thresholds: t } = data
    const temp = toPoints(items, (m) => m.temp_c, (v) => tempOutOfRange(v, t))
    const spo2 = toPoints(items, (m) => m.spo2, (v) => spo2OutOfRange(v, t))
    const bpm = toPoints(items, (m) => m.bpm)
    const weight = toPoints(items, (m) => m.weight_kg)
    const tempBand = { from: t.temp_low_c, to: t.temp_high_c }
    const spo2Band = { from: t.spo2_min, to: 100 }
    return {
      temp,
      spo2,
      bpm,
      weight,
      tempBand,
      spo2Band,
      tempDomain: paddedDomain(temp.map((p) => p.value), tempBand),
      spo2Domain: paddedDomain(spo2.map((p) => p.value), spo2Band, 100),
      bpmDomain: paddedDomain(bpm.map((p) => p.value)),
      weightDomain: paddedDomain(weight.map((p) => p.value)),
    }
  }, [data])

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

  const items = data?.items ?? []
  const latest = items.at(-1)
  const thresholds = data?.thresholds
  const title = patient?.name || `Paciente ${code}`
  const details = [code, patient?.age != null ? `${patient.age} años` : '', latest ? `última medición ${formatDateTime(latest.ts)}` : '']
    .filter(Boolean)
    .join(' · ')

  return (
    <>
      <Link
        to="/patients"
        className="text-muted-foreground hover:text-foreground flex w-fit items-center gap-1 text-sm transition-colors"
      >
        <ArrowLeft className="size-4" />
        Pacientes
      </Link>
      <PageHeader title={title} description={details} />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <RangeFilter value={days} onChange={setDays} />
        <div className="flex flex-wrap items-center gap-3">
          {data && (
            <p className="text-muted-foreground text-sm">
              {items.length === 1 ? '1 medición' : `${items.length} mediciones`}
            </p>
          )}
          <Button size="sm" variant="outline" nativeButton={false} render={<Link to={`/patients/${encodeURIComponent(code)}/monitor`} />}>
            <MonitorPlay className="size-4" />
            Vista de monitor
          </Button>
          <Button size="sm" disabled={exporter.busy !== null} onClick={() => exporter.download('xlsx')}>
            <FileSpreadsheet className="size-4" />
            {exporter.busy === 'xlsx' ? 'Preparando…' : 'Descargar Excel'}
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={exporter.busy !== null}
            onClick={() => exporter.download('csv')}
          >
            <Download className="size-4" />
            {exporter.busy === 'csv' ? 'Preparando…' : 'CSV'}
          </Button>
        </div>
      </div>

      {exporter.error && (
        <Alert variant="destructive">
          <AlertDescription>{exporter.error}</AlertDescription>
        </Alert>
      )}

      {data && items.length === 0 && !loading && (
        <Alert>
          <AlertDescription>
            No hay mediciones en este rango.
            {days !== null && ' Prueba con un rango más amplio o con «Todo».'}
          </AlertDescription>
        </Alert>
      )}

      {latest && thresholds && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Temperatura"
            value={`${formatNumber(latest.temp_c, 1)} °C`}
            hint={tempOutOfRange(latest.temp_c, thresholds) ? 'Fuera de rango' : 'Dentro del rango'}
            icon={Thermometer}
            alert={tempOutOfRange(latest.temp_c, thresholds)}
            onInfo={() => showInfo('temperature')}
          />
          <StatCard
            title="Oxigenación (SpO₂)"
            value={`${latest.spo2} %`}
            hint={spo2OutOfRange(latest.spo2, thresholds) ? 'Fuera de rango' : 'Dentro del rango'}
            icon={Activity}
            alert={spo2OutOfRange(latest.spo2, thresholds)}
            onInfo={() => showInfo('spo2')}
          />
          <StatCard title="Pulso" value={`${latest.bpm} lpm`} hint="Última medición" icon={HeartPulse} />
          <StatCard
            title="Peso"
            value={`${formatNumber(latest.weight_kg, 1)} kg`}
            hint="Última medición"
            icon={Scale}
            onInfo={() => showInfo('weight')}
          />
        </div>
      )}

      {summary && <SummaryPanel summary={summary} />}

      {charts && thresholds && (
        <div className="grid gap-4 lg:grid-cols-2">
          <MetricChart
            title="Temperatura"
            unit="°C"
            decimals={1}
            points={charts.temp}
            band={charts.tempBand}
            bandText={`Sin alerta: entre ${thresholds.temp_low_c} y ${thresholds.temp_high_c} °C`}
            domain={charts.tempDomain}
            dimmed={loading}
          />
          <MetricChart
            title="Oxigenación (SpO₂)"
            unit="%"
            decimals={0}
            points={charts.spo2}
            band={charts.spo2Band}
            bandText={`Sin alerta: ${thresholds.spo2_min} % o más`}
            domain={charts.spo2Domain}
            dimmed={loading}
          />
          <MetricChart title="Pulso" unit="lpm" decimals={0} points={charts.bpm} domain={charts.bpmDomain} dimmed={loading} />
          <MetricChart
            title="Peso"
            unit="kg"
            decimals={1}
            points={charts.weight}
            domain={charts.weightDomain}
            dimmed={loading}
          />
        </div>
      )}

      {items.length > 0 && (
        <TempPulseScatter items={items} r={summary?.correlation?.temp_bpm?.r ?? null} n={summary?.correlation?.temp_bpm?.n ?? 0} />
      )}

      {items.length > 0 && thresholds && <MeasurementsTable items={items} thresholds={thresholds} />}

      <VitalInfoDialog vital={infoVital} open={infoOpen} onOpenChange={setInfoOpen} thresholds={thresholds} />
    </>
  )
}
