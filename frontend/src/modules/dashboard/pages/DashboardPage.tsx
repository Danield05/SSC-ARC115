import { BellRing, Cpu, UserCog, UsersRound } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { useDevices } from '@/modules/admin/hooks/useDevices'
import { useUsers } from '@/modules/admin/hooks/useUsers'
import { useAuth } from '@/modules/auth/hooks/useAuth'
import { useAlertsSummary } from '@/modules/measurements/hooks/useAlertsSummary'
import { usePatients } from '@/modules/patients/hooks/usePatients'
import { ROLE_LABELS } from '@/modules/auth/types'
import { assetUrl } from '@/lib/utils'
import PageHeader from '@/shared/components/PageHeader'
import StatCard from '@/shared/components/StatCard'
import VitalGuide from '../components/VitalGuide'

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`

/** Alertas de los últimos 7 días de lo que el rol puede ver; enlaza a la más reciente o a la bandeja. */
function AlertsStat() {
  const { data, loading } = useAlertsSummary()
  const total = data ? data.alerts + data.unassigned_alerts : 0
  const days = data?.days ?? 7

  let value = '—'
  let hint = 'Sin datos por ahora'
  let link: { to: string; label: string } | undefined
  if (loading) {
    value = '…'
    hint = 'Cargando…'
  } else if (data && data.measurements === 0) {
    hint = `Sin mediciones en los últimos ${days} días`
  } else if (data) {
    value = String(total)
    const unassigned = data.unassigned_alerts > 0 ? ` · ${data.unassigned_alerts} sin asignar` : ''
    hint = `${plural(data.alerts, 'alerta', 'alertas')} en ${days} días${unassigned}`
    if (data.latest) {
      const code = data.latest.patient_code
      link = { to: `/patients/${encodeURIComponent(code)}/alertas`, label: `Ver ${code}` }
    } else if (data.unassigned_alerts > 0) {
      link = { to: '/sin-asignar', label: 'Ver sin asignar' }
    }
  }
  return <StatCard title="Alertas" value={value} hint={hint} icon={BellRing} alert={total > 0} link={link} />
}

function UsersStat() {
  const { users, loading } = useUsers()
  const active = users.filter((u) => u.active).length
  return (
    <StatCard
      title="Usuarios activos"
      value={loading ? '…' : String(active)}
      hint={`${users.length} registrados en total`}
      icon={UserCog}
    />
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { devices, loading } = useDevices()
  const { patients, loading: loadingPatients } = usePatients()
  if (!user) return null
  const active = devices.filter((d) => d.active).length

  return (
    <>
      <PageHeader
        title="Resumen"
        description={`Sesión como ${ROLE_LABELS[user.role].toLowerCase()}. Estado general del sistema.`}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Dispositivos activos"
          value={loading ? '…' : String(active)}
          hint={`${devices.length} registrados`}
          icon={Cpu}
        />
        {user.role === 'admin' && <UsersStat />}
        <StatCard
          title="Pacientes"
          value={loadingPatients ? '…' : String(patients.length)}
          hint={patients.length === 0 ? 'Registra el primero en la sección Pacientes' : 'Registrados en el sistema'}
          icon={UsersRound}
        />
        <AlertsStat />
      </div>

      <Card className="overflow-hidden">
        <div className="grid sm:grid-cols-5">
          <div className="relative h-48 sm:col-span-2 sm:h-auto sm:min-h-56">
            <img
              src={assetUrl('images/oximetro.jpg')}
              alt="Oxímetro de dedo mostrando saturación de oxígeno y pulso"
              className="absolute inset-0 size-full object-cover"
            />
          </div>
          <div className="flex flex-col justify-center space-y-3 p-6 sm:col-span-3">
            <h2 className="text-lg font-semibold">Un dispositivo, tres mediciones</h2>
            <p className="text-muted-foreground text-sm">
              El promotor mide peso, temperatura y oxigenación en sangre. Cada medición se guarda en el aparato aunque
              no haya internet y se envía sola cuando vuelve la conexión.
            </p>
          </div>
        </div>
      </Card>

      <VitalGuide />
    </>
  )
}
