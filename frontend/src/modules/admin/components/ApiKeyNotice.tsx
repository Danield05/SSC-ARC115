import { useState } from 'react'

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
    <div className="notice">
      <p>
        <strong>Clave de {deviceId}.</strong> Cópiala ahora: no se vuelve a mostrar. Va en el{' '}
        <code>secrets.h</code> del firmware.
      </p>
      <code className="key">{apiKey}</code>
      <div className="row">
        <button type="button" onClick={copy}>
          {copied ? 'Copiada' : 'Copiar'}
        </button>
        <button type="button" className="secondary" onClick={onClose}>
          Ya la guardé
        </button>
      </div>
    </div>
  )
}
