import { ArrowLeft, HeartPulse } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import SplashScreen from '@/shared/components/SplashScreen'
import { usePageReady } from '@/shared/hooks/usePageReady'
import { assetUrl } from '@/lib/utils'

interface Props {
  title: string
  description: string
  /** Archivo dentro de public/images/ para el panel lateral. */
  image: string
  imageAlt: string
  quote: string
  /** Muestra la animación de carga mientras llegan las imágenes (solo la primera vez). */
  splash?: boolean
  children: ReactNode
}

/** Marco común de las pantallas de acceso: formulario a la izquierda y fotografía a la derecha. */
export default function AuthShell({ title, description, image, imageAlt, quote, splash, children }: Props) {
  const imageUrl = assetUrl(`images/${image}`)
  const ready = usePageReady([imageUrl], 900, !!splash)

  return (
    <>
      {splash && <SplashScreen ready={ready} />}
      <div className="grid min-h-svh lg:grid-cols-2">
        <div className="flex flex-col gap-6 p-6 md:p-10">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 font-semibold">
              <div className="bg-primary text-primary-foreground flex size-8 items-center justify-center rounded-lg">
                <HeartPulse className="size-5" />
              </div>
              SSC-ARC115
            </Link>
            <Link
              to="/"
              className="text-muted-foreground hover:text-foreground flex items-center gap-1 text-sm transition-colors"
            >
              <ArrowLeft className="size-4" />
              Inicio
            </Link>
          </div>
          <div className="flex flex-1 items-center justify-center">
            <div className="rise-in w-full max-w-sm space-y-6">
              <div className="space-y-1">
                <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
                <p className="text-muted-foreground text-sm">{description}</p>
              </div>
              {children}
            </div>
          </div>
          <p className="text-muted-foreground text-xs">
            Proyecto académico ARC115 · Universidad de El Salvador en Línea. Este sistema registra y da
            seguimiento; no emite diagnósticos médicos.
          </p>
        </div>
        <div className="relative hidden lg:block">
          <img src={imageUrl} alt={imageAlt} className="absolute inset-0 size-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/10 to-transparent" />
          <div className="absolute inset-x-0 bottom-0 p-10 text-white">
            <p className="text-2xl leading-snug font-semibold">{quote}</p>
          </div>
        </div>
      </div>
    </>
  )
}
