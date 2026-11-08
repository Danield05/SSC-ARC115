import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import VitalInfoDialog from '@/shared/components/VitalInfoDialog'
import { VITAL_KEYS, getVitalInfo } from '@/shared/vitals/vitalInfo'
import type { VitalKey } from '@/shared/vitals/vitalInfo'

/** «Qué mide cada valor y por qué importa»: una tarjeta por valor con su ventana «Más información». */
export default function VitalGuide() {
  const [vital, setVital] = useState<VitalKey>('weight')
  const [open, setOpen] = useState(false)

  function show(key: VitalKey) {
    setVital(key)
    setOpen(true)
  }

  return (
    <section aria-labelledby="vital-guide-title" className="space-y-4">
      <h2 id="vital-guide-title" className="text-lg font-semibold">
        Qué mide cada valor y por qué importa
      </h2>

      <div className="grid gap-4 md:grid-cols-3">
        {VITAL_KEYS.map((key) => {
          const info = getVitalInfo(key)
          const Icon = info.icon
          return (
            <Card key={key} className="h-full">
              <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                <div className="bg-accent text-accent-foreground flex size-8 shrink-0 items-center justify-center rounded-lg">
                  <Icon className="size-4" aria-hidden />
                </div>
                <CardTitle className="text-base font-semibold">{info.title}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col items-start gap-3 text-sm">
                <p className="text-muted-foreground">{info.summary}</p>
                <Badge variant={info.badge.alert ? 'destructive' : 'secondary'} className="h-auto py-1 whitespace-normal">
                  {info.badge.text}
                </Badge>
                <Button
                  type="button"
                  variant="link"
                  className="mt-auto h-auto p-0"
                  aria-haspopup="dialog"
                  aria-label={`Más información sobre ${info.title}`}
                  onClick={() => show(key)}
                >
                  Más información
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <p className="text-muted-foreground text-center text-xs">
        Información orientativa. Ante una alerta, consulta a un profesional de salud.
      </p>

      <VitalInfoDialog vital={vital} open={open} onOpenChange={setOpen} />
    </section>
  )
}
