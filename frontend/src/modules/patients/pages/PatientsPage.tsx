import { LineChart } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import PageHeader from '@/shared/components/PageHeader'

export default function PatientsPage() {
  return (
    <>
      <PageHeader title="Pacientes" description="Historial de mediciones por código de paciente." />
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
          <div className="bg-accent text-accent-foreground flex size-12 items-center justify-center rounded-full">
            <LineChart className="size-6" />
          </div>
          <h2 className="text-lg font-semibold">Aún no hay mediciones</h2>
          <p className="text-muted-foreground max-w-md text-sm">
            Cuando un dispositivo sincronice sus primeras mediciones, aquí verás la lista de pacientes y las
            gráficas de temperatura, oxigenación, pulso y peso.
          </p>
        </CardContent>
      </Card>
    </>
  )
}
