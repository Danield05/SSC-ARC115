import { Check, Copy, KeyRound } from 'lucide-react'
import { useState } from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

interface Props {
  deviceId: string
  apiKey: string
  onClose: () => void
}

export default function ApiKeyNotice({ deviceId, apiKey, onClose }: Props) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(apiKey)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  return (
    <Alert className="border-warning/50 bg-warning/10">
      <KeyRound />
      <AlertTitle>Clave de {deviceId}</AlertTitle>
      <AlertDescription className="space-y-3">
        <p>
          Cópiala ahora: no se vuelve a mostrar. Va en el <code>secrets.h</code> del firmware.
        </p>
        <code className="bg-background block rounded-md border px-3 py-2 text-xs break-all">{apiKey}</code>
        <div className="flex gap-2">
          <Button size="sm" onClick={copy}>
            {copied ? <Check /> : <Copy />}
            {copied ? 'Copiada' : 'Copiar'}
          </Button>
          <Button size="sm" variant="outline" onClick={onClose}>
            Ya la guardé
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  )
}
