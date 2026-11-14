import { lazy, Suspense, useState } from 'react'
import { BellRing, Cpu, UserCog, UsersRound } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
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

const PrototypeViewer = lazy(() => import('../components/PrototypeViewer'))

const PHOTOS = [
  { file: 'prototipo-soporte.jpg', alt: 'Soporte con báscula y caja de control', fit: 'object-cover object-top' },
  { file: 'prototipo-panel.jpg', alt: 'Panel con botón y LEDs de semáforo', fit: 'object-cover object-top' },
  { file: 'prototipo-circuito.jpg', alt: 'Circuito con ESP32 y sensores', fit: 'object-cover' },
]

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
  const [zoom, setZoom] = useState<(typeof PHOTOS)[number] | null>(null)
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

      <Card className="gap-0 overflow-hidden py-0">
        <div className="grid lg:grid-cols-5">
          <div className="flex flex-col justify-center space-y-3 p-6 lg:col-span-2">
            <h2 className="text-lg font-semibold">Un dispositivo, tres mediciones</h2>
            <p className="text-muted-foreground text-sm">
              El promotor mide peso, temperatura y oxigenación en sangre. Cada medición se guarda en el aparato aunque
              no haya internet y se envía sola cuando vuelve la conexión.
            </p>
            <div className="grid grid-cols-3 gap-2 pt-2">
              {PHOTOS.map((photo) => (
                <button
                  key={photo.file}
                  type="button"
                  onClick={() => setZoom(photo)}
                  aria-label={`Ampliar: ${photo.alt}`}
                  className="ring-foreground/10 focus-visible:ring-ring aspect-square cursor-zoom-in overflow-hidden rounded-md ring-1 outline-none focus-visible:ring-2"
                >
                  <img
                    src={assetUrl(`images/${photo.file}`)}
                    alt=""
                    loading="lazy"
                    className={`size-full transition-transform duration-200 hover:scale-105 ${photo.fit}`}
                  />
                </button>
              ))}
            </div>
          </div>
          <div className="bg-muted/40 lg:col-span-3">
            <Suspense fallback={<div className="h-80 lg:h-full" />}>
              <PrototypeViewer />
            </Suspense>
          </div>
        </div>
      </Card>

      <Dialog open={zoom !== null} onOpenChange={(open) => !open && setZoom(null)}>
        <DialogContent className="sm:max-w-3xl">
          <DialogTitle>{zoom?.alt}</DialogTitle>
          {zoom && (
            <img
              src={assetUrl(`images/${zoom.file}`)}
              alt={zoom.alt}
              className="mx-auto max-h-[75vh] w-auto max-w-full rounded-md object-contain"
            />
          )}
        </DialogContent>
      </Dialog>

      <VitalGuide />
    </>
  )
}
