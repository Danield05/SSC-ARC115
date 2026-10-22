import { useEffect, useState } from 'react'

// La pantalla de carga se muestra una vez por carga de la página: al pasar de la portada al
// login dentro de la misma sesión no vuelve a aparecer.
let splashShown = false

const MAX_WAIT_MS = 4000

function preload(url: string): Promise<void> {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve()
    img.onerror = () => resolve()
    img.src = url
  })
}

/**
 * Devuelve `true` cuando las imágenes ya cargaron y pasó el tiempo mínimo de la animación.
 * Si la pantalla de carga ya se mostró antes, devuelve `true` desde el primer render.
 */
export function usePageReady(imageUrls: string[], minMs = 900, enabled = true): boolean {
  const [ready, setReady] = useState(splashShown || !enabled)
  const key = imageUrls.join('|')

  useEffect(() => {
    if (splashShown || !enabled) return
    let cancelled = false
    const images = Promise.race([
      Promise.all((key ? key.split('|') : []).map(preload)),
      new Promise<void>((resolve) => setTimeout(resolve, MAX_WAIT_MS)),
    ])
    const minimum = new Promise<void>((resolve) => setTimeout(resolve, minMs))
    Promise.all([images, minimum]).then(() => {
      if (cancelled) return
      splashShown = true
      setReady(true)
    })
    return () => {
      cancelled = true
    }
  }, [key, minMs, enabled])

  return ready
}
