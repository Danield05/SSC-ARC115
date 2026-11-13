import {
  Activity,
  ArrowRight,
  BellRing,
  Cloud,
  HardDrive,
  HeartPulse,
  LineChart,
  Mail,
  Scale,
  ShieldCheck,
  Thermometer,
  WifiOff,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { buttonVariants } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { assetUrl } from '@/lib/utils'
import SplashScreen from '@/shared/components/SplashScreen'
import ThemeToggle from '@/shared/components/ThemeToggle'
import { usePageReady } from '@/shared/hooks/usePageReady'
import { useAuth } from '../../auth/hooks/useAuth'

const img = (file: string) => assetUrl(`images/${file}`)

const HERO = img('visita-domiciliaria.jpg')

const MEASURES: { icon: LucideIcon; title: string; sensor: string; text: string }[] = [
  {
    icon: Thermometer,
    title: 'Temperatura corporal',
    sensor: 'Termistor NTC',
    text: 'De contacto: se apoya sobre la piel y mide su temperatura. Avisa cuando es de 35 °C o menos, o de 38 °C o más.',
  },
  {
    icon: Activity,
    title: 'Oxigenación y pulso',
    sensor: 'Sensor MAX30102',
    text: 'Saturación de oxígeno (SpO₂) y pulsaciones por minuto con un dedo. Avisa si la SpO₂ baja de 92 %.',
  },
  {
    icon: Scale,
    title: 'Peso',
    sensor: 'Celdas de carga + HX711',
    text: 'Báscula integrada al dispositivo para seguir la evolución del peso en cada visita.',
  },
]

const STEPS: { icon: LucideIcon; title: string; text: string }[] = [
  {
    icon: HeartPulse,
    title: 'Mide',
    text: 'El promotor toma temperatura, oxigenación, pulso y peso con el dispositivo, en la casa del paciente.',
  },
  {
    icon: HardDrive,
    title: 'Guarda',
    text: 'Cada medición queda en la memoria interna del equipo, haya o no internet. Nada se pierde.',
  },
  {
    icon: Cloud,
    title: 'Sincroniza',
    text: 'Cuando hay Wi-Fi, el lote pendiente viaja cifrado (HTTPS) a la nube sin duplicar registros.',
  },
  {
    icon: Mail,
    title: 'Avisa y muestra',
    text: 'El promotor recibe un correo con las alertas, y el historial queda en gráficas por paciente.',
  },
]

const GALLERY = [
  { file: 'visita-rural.jpg', alt: 'Promotor de salud con una tablilla conversando con una vecina en el patio de su casa' },
  { file: 'educacion-salud.jpg', alt: 'Promotora de salud explicando un folleto a una joven en su hogar' },
  { file: 'equipo-en-campo.jpg', alt: 'Equipo de promotores de salud caminando por una comunidad rural' },
]

function SectionTitle({ eyebrow, title, text }: { eyebrow: string; title: string; text?: string }) {
  return (
    <div className="mx-auto max-w-2xl space-y-3 text-center">
      <p className="text-primary text-sm font-semibold tracking-wide uppercase">{eyebrow}</p>
      <h2 className="text-3xl font-semibold tracking-tight text-balance">{title}</h2>
      {text && <p className="text-muted-foreground text-balance">{text}</p>}
    </div>
  )
}

export default function LandingPage() {
  const { user } = useAuth()
  const ready = usePageReady([HERO], 1000)
  const enterTo = user ? '/dashboard' : '/login'
  const enterLabel = user ? 'Ir al panel' : 'Ingresar'

  return (
    <>
      <SplashScreen ready={ready} />
      <div className="bg-background min-h-svh">
        <header className="bg-background/80 sticky top-0 z-30 border-b backdrop-blur">
          <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4 md:px-6">
            <Link to="/" className="flex items-center gap-2 font-semibold">
              <span className="bg-primary text-primary-foreground flex size-8 items-center justify-center rounded-lg">
                <HeartPulse className="size-5" />
              </span>
              SSC-ARC115
            </Link>
            <nav className="text-muted-foreground ml-6 hidden items-center gap-6 text-sm md:flex">
              <a href="#que-mide" className="hover:text-foreground transition-colors">
                Qué mide
              </a>
              <a href="#como-funciona" className="hover:text-foreground transition-colors">
                Cómo funciona
              </a>
              <a href="#alertas" className="hover:text-foreground transition-colors">
                Alertas
              </a>
            </nav>
            <div className="ml-auto flex items-center gap-2">
              <ThemeToggle />
              <Link to={enterTo} className={buttonVariants({ size: 'lg' })}>
                {enterLabel}
              </Link>
            </div>
          </div>
        </header>

        <main>
          <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 md:px-6 lg:grid-cols-2 lg:py-20">
            <div className="rise-in space-y-6">
              <span className="bg-accent text-accent-foreground inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium">
                <WifiOff className="size-3.5" />
                Funciona también sin internet
              </span>
              <h1 className="text-4xl font-semibold tracking-tight text-balance md:text-5xl">
                Los signos vitales de tu comunidad, medidos a tiempo y a salvo.
              </h1>
              <p className="text-muted-foreground max-w-xl text-lg text-pretty">
                Un dispositivo portátil que mide temperatura, oxigenación, pulso y peso en la visita
                domiciliaria, guarda todo aunque no haya señal y avisa por correo cuando algo se sale de lo
                normal.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link to={enterTo} className={buttonVariants({ size: 'lg', className: 'h-10 px-5 text-base' })}>
                  {enterLabel}
                  <ArrowRight />
                </Link>
                <a
                  href="#como-funciona"
                  className={buttonVariants({ variant: 'outline', size: 'lg', className: 'h-10 px-5 text-base' })}
                >
                  Ver cómo funciona
                </a>
              </div>
            </div>
            <div className="rise-in relative" style={{ animationDelay: '0.15s' }}>
              <img
                src={HERO}
                alt="Promotores de salud con mascarilla anotando datos durante una visita casa por casa"
                className="aspect-[4/3] w-full rounded-2xl object-cover shadow-xl"
              />
              <div className="bg-card absolute -bottom-5 left-4 flex items-center gap-3 rounded-xl border p-3 shadow-lg">
                <span className="bg-primary/10 text-primary flex size-9 items-center justify-center rounded-lg">
                  <BellRing className="size-5" />
                </span>
                <div className="text-sm leading-tight">
                  <p className="font-medium">Alerta al promotor</p>
                  <p className="text-muted-foreground text-xs">por correo, en cada sincronización</p>
                </div>
              </div>
            </div>
          </section>

          <section id="que-mide" className="bg-muted/40 scroll-mt-16 border-y py-16">
            <div className="mx-auto max-w-6xl space-y-10 px-4 md:px-6">
              <SectionTitle
                eyebrow="Qué mide"
                title="Tres parámetros, un solo equipo"
                text="Lo esencial para el seguimiento comunitario, sin complicar la visita."
              />
              <div className="grid gap-4 md:grid-cols-3">
                {MEASURES.map((m) => (
                  <Card key={m.title}>
                    <CardContent className="space-y-3 pt-6">
                      <span className="bg-primary/10 text-primary flex size-11 items-center justify-center rounded-xl">
                        <m.icon className="size-6" />
                      </span>
                      <h3 className="text-lg font-semibold">{m.title}</h3>
                      <p className="text-primary text-xs font-medium">{m.sensor}</p>
                      <p className="text-muted-foreground text-sm">{m.text}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </section>

          <section id="como-funciona" className="mx-auto max-w-6xl scroll-mt-16 space-y-10 px-4 py-16 md:px-6">
            <SectionTitle
              eyebrow="Cómo funciona"
              title="Del hogar del paciente a tu correo"
              text="Primero se guarda, después se envía: la comunidad no depende de la señal."
            />
            <ol className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {STEPS.map((s, i) => (
                <li key={s.title} className="relative space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="bg-primary text-primary-foreground flex size-10 items-center justify-center rounded-full text-sm font-semibold">
                      {i + 1}
                    </span>
                    <s.icon className="text-primary size-6" />
                  </div>
                  <h3 className="text-lg font-semibold">{s.title}</h3>
                  <p className="text-muted-foreground text-sm">{s.text}</p>
                </li>
              ))}
            </ol>
          </section>

          <section className="mx-auto max-w-6xl px-4 pb-16 md:px-6">
            <div className="grid gap-4 md:grid-cols-3">
              {GALLERY.map((g) => (
                <img
                  key={g.file}
                  src={img(g.file)}
                  alt={g.alt}
                  loading="lazy"
                  className="aspect-[4/3] w-full rounded-xl object-cover"
                />
              ))}
            </div>
            <p className="text-muted-foreground mt-4 text-center text-sm">
              Pensado para el trabajo de campo de los promotores de salud.
            </p>
          </section>

          <section id="alertas" className="bg-muted/40 scroll-mt-16 border-y py-16">
            <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 md:px-6 lg:grid-cols-2">
              <img
                src={img('registro-movil.jpg')}
                alt="Dos promotoras de salud revisando datos en un teléfono durante una visita"
                loading="lazy"
                className="aspect-[4/3] w-full rounded-2xl object-cover"
              />
              <div className="space-y-5">
                <p className="text-primary text-sm font-semibold tracking-wide uppercase">Alertas por umbral</p>
                <h2 className="text-3xl font-semibold tracking-tight text-balance">
                  Un aviso claro cuando un valor se sale del rango
                </h2>
                <ul className="space-y-3 text-sm">
                  <li className="flex gap-3">
                    <Thermometer className="text-primary mt-0.5 size-5 shrink-0" />
                    <span>
                      <strong>Temperatura</strong> de 35 °C o menos, o de 38 °C o más.
                    </span>
                  </li>
                  <li className="flex gap-3">
                    <Activity className="text-primary mt-0.5 size-5 shrink-0" />
                    <span>
                      <strong>Saturación de oxígeno (SpO₂)</strong> por debajo de 92 %.
                    </span>
                  </li>
                  <li className="flex gap-3">
                    <LineChart className="text-primary mt-0.5 size-5 shrink-0" />
                    <span>
                      <strong>Historial en gráficas</strong> por paciente para ver la tendencia entre visitas.
                    </span>
                  </li>
                  <li className="flex gap-3">
                    <ShieldCheck className="text-primary mt-0.5 size-5 shrink-0" />
                    <span>
                      <strong>Privacidad:</strong> el dispositivo solo guarda un código; los datos personales viven
                      en el sistema web y cada promotor ve solo a sus pacientes.
                    </span>
                  </li>
                </ul>
                <p className="text-muted-foreground border-l-2 pl-3 text-xs">
                  Este sistema registra y da seguimiento; no emite diagnósticos médicos. Ante cualquier duda de
                  salud, consulta a un profesional.
                </p>
              </div>
            </div>
          </section>

          <section className="mx-auto max-w-6xl px-4 py-16 text-center md:px-6">
            <div className="bg-primary text-primary-foreground space-y-5 rounded-2xl px-6 py-12">
              <h2 className="text-3xl font-semibold tracking-tight text-balance">¿Listo para consultar a tu comunidad?</h2>
              <p className="mx-auto max-w-xl text-pretty opacity-90">
                Entra con el correo con el que el equipo te dio acceso. Si es tu primera vez, te llegó una
                contraseña provisional.
              </p>
              <Link
                to={enterTo}
                className={buttonVariants({ variant: 'secondary', size: 'lg', className: 'h-10 px-6 text-base' })}
              >
                {enterLabel}
                <ArrowRight />
              </Link>
            </div>
          </section>
        </main>

        <footer className="text-muted-foreground border-t px-4 py-8 text-center text-xs md:px-6">
          <p className="text-foreground font-medium">SSC-ARC115 · Dispositivo de monitoreo de salud comunitario</p>
          <p className="mt-1">
            Grupo 3 (GP03) · ARC115 Arquitectura de Computadoras · Universidad de El Salvador en Línea · 2026
          </p>
          <p className="mt-1">Este sistema registra y da seguimiento; no emite diagnósticos médicos.</p>
        </footer>
      </div>
    </>
  )
}
