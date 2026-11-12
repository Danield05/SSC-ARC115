import { useEffect, useRef } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'

const TABS = [
  { path: '', label: 'Historial', end: true },
  { path: '/monitor', label: 'Monitor', end: false },
  { path: '/analisis', label: 'Análisis', end: false },
  { path: '/trazabilidad', label: 'Trazabilidad', end: false },
  { path: '/episodios', label: 'Episodios', end: false },
  { path: '/alertas', label: 'Alertas', end: false },
]

/** Sub-navegación del paciente. Cada pestaña es una ruta: el botón Atrás y los enlaces directos funcionan. */
export default function PatientTabs({ code }: { code: string }) {
  const root = `/patients/${encodeURIComponent(code)}`
  const nav = useRef<HTMLElement>(null)
  const { pathname } = useLocation()
  // En pantallas angostas la barra se desplaza: la pestaña activa siempre queda a la vista.
  useEffect(() => {
    nav.current?.querySelector('[aria-current="page"]')?.scrollIntoView({ inline: 'center', block: 'nearest' })
  }, [pathname])
  return (
    <nav ref={nav} aria-label="Secciones del paciente" className="flex gap-0.5 overflow-x-auto border-b sm:gap-1">
      {TABS.map((tab) => (
        <NavLink
          key={tab.label}
          to={`${root}${tab.path}`}
          end={tab.end}
          className={({ isActive }) =>
            cn(
              '-mb-px border-b-2 px-2 py-2 text-[13px] font-medium whitespace-nowrap transition-colors sm:px-4 sm:text-sm',
              isActive ? 'border-primary text-foreground' : 'text-muted-foreground hover:text-foreground border-transparent',
            )
          }
        >
          {tab.label}
        </NavLink>
      ))}
    </nav>
  )
}
