import { Outlet, useLocation } from 'react-router-dom'
import { Separator } from '@/components/ui/separator'
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import AppSidebar from './AppSidebar'
import SiteFooter from './SiteFooter'
import ThemeToggle from './ThemeToggle'

const TITLES: Record<string, string> = {
  '/dashboard': 'Resumen',
  '/patients': 'Pacientes',
  '/admin/devices': 'Dispositivos',
  '/admin/users': 'Usuarios',
}

/** Título de la barra superior en las páginas del paciente: sigue a la pestaña abierta. */
function patientTitle(pathname: string) {
  if (pathname.endsWith('/monitor')) return 'Monitor del paciente'
  if (pathname.endsWith('/analisis')) return 'Análisis del paciente'
  if (pathname.endsWith('/trazabilidad')) return 'Trazabilidad del paciente'
  if (pathname.endsWith('/episodios')) return 'Episodios del paciente'
  if (pathname.endsWith('/alertas')) return 'Alertas del paciente'
  return 'Historial del paciente'
}

export default function Layout() {
  const { pathname } = useLocation()

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="bg-background/80 sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b px-4 backdrop-blur">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 data-vertical:h-4 data-vertical:self-center" />
          <span className="text-sm font-medium">
            {TITLES[pathname] ?? (pathname.startsWith('/patients/') ? patientTitle(pathname) : '')}
          </span>
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 p-4 md:p-6">
          <Outlet />
        </main>
        <SiteFooter />
      </SidebarInset>
    </SidebarProvider>
  )
}
