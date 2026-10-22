import { Activity, BellRing, Cpu, Scale, Thermometer, UserCog, UsersRound } from 'lucide-react'
import { Card, CardDescription, CardHeader, CardContent, CardTitle } from '@/components/ui/card'
import { useDevices } from '@/modules/admin/hooks/useDevices'
import { useUsers } from '@/modules/admin/hooks/useUsers'
import { useAuth } from '@/modules/auth/hooks/useAuth'
import { ROLE_LABELS } from '@/modules/auth/types'
import { assetUrl } from '@/lib/utils'
import PageHeader from '@/shared/components/PageHeader'
import StatCard from '@/shared/components/StatCard'

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

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="overflow-hidden lg:col-span-2">
          <div className="grid sm:grid-cols-5">
            <img
              src={assetUrl('images/oximetro.jpg')}
              alt="Oxímetro de dedo mostrando saturación de oxígeno y pulso"
              className="h-48 w-full object-cover sm:col-span-2 sm:h-full"
            />
            <div className="space-y-3 p-6 sm:col-span-3">
              <h2 className="text-lg font-semibold">Un dispositivo, tres mediciones</h2>
              <p className="text-muted-foreground text-sm">
                El promotor mide temperatura, oxígeno en sangre con pulso, y peso. Cada medición se guarda en el
                aparato aunque no haya internet y se envía sola cuando vuelve la conexión.
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Alertas por umbral</CardTitle>
            <CardDescription>Valores que activan el aviso por correo.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex items-start gap-3">
              <Thermometer className="text-primary mt-0.5 size-5" />
              <div>
                <p className="font-medium">Temperatura</p>
                <p className="text-muted-foreground">35 °C o menos, o 38 °C o más</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Activity className="text-primary mt-0.5 size-5" />
              <div>
                <p className="font-medium">Oxigenación (SpO₂)</p>
                <p className="text-muted-foreground">Menos de 92 %</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Scale className="text-primary mt-0.5 size-5" />
              <div>
                <p className="font-medium">Peso</p>
                <p className="text-muted-foreground">Solo seguimiento, sin umbral</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  )
}
