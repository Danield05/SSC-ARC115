import { BellRing, Cpu, UserCog, UsersRound } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { useDevices } from '@/modules/admin/hooks/useDevices'
import { useUsers } from '@/modules/admin/hooks/useUsers'
import { useAuth } from '@/modules/auth/hooks/useAuth'
import { ROLE_LABELS } from '@/modules/auth/types'
import { assetUrl } from '@/lib/utils'
import PageHeader from '@/shared/components/PageHeader'
import StatCard from '@/shared/components/StatCard'
import VitalGuide from '../components/VitalGuide'

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
        <StatCard title="Pacientes" value="—" hint="Aparecerán con la primera sincronización" icon={UsersRound} />
        <StatCard title="Alertas" value="—" hint="Sin mediciones todavía" icon={BellRing} />
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
