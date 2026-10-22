import { Cpu, HeartPulse, KeyRound, LayoutDashboard, LogOut, UserCog, UsersRound } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar'
import { useAuth } from '@/modules/auth/hooks/useAuth'
import { ROLE_LABELS } from '@/modules/auth/types'
import type { Role } from '@/modules/auth/types'

interface NavItem {
  title: string
  url: string
  icon: LucideIcon
  roles: Role[]
}

const ALL: Role[] = ['admin', 'promoter', 'viewer']

const GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: 'Principal',
    items: [
      { title: 'Resumen', url: '/dashboard', icon: LayoutDashboard, roles: ALL },
      { title: 'Pacientes', url: '/patients', icon: UsersRound, roles: ALL },
    ],
  },
  {
    label: 'Administración',
    items: [
      { title: 'Dispositivos', url: '/admin/devices', icon: Cpu, roles: ['admin', 'viewer'] },
      { title: 'Usuarios', url: '/admin/users', icon: UserCog, roles: ['admin'] },
    ],
  },
]

function UserMenu() {
  const { user, logout } = useAuth()
  const { isMobile } = useSidebar()
  if (!user) return null

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger
            render={<SidebarMenuButton size="lg" className="data-popup-open:bg-sidebar-accent cursor-pointer" />}
          >
            <div className="bg-primary text-primary-foreground flex size-8 items-center justify-center rounded-lg text-sm font-semibold">
              {user.email.charAt(0).toUpperCase()}
            </div>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium">{user.email}</span>
              <span className="text-muted-foreground truncate text-xs">{ROLE_LABELS[user.role]}</span>
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--anchor-width) min-w-56 rounded-lg"
            side={isMobile ? 'bottom' : 'right'}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuGroup>
              <DropdownMenuLabel className="text-muted-foreground text-xs font-normal">
                Sesión iniciada como {ROLE_LABELS[user.role]}
              </DropdownMenuLabel>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem className="cursor-pointer" render={<Link to="/change-password" />}>
                <KeyRound />
                Cambiar contraseña
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer" onClick={logout}>
                <LogOut />
                Cerrar sesión
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}

export default function AppSidebar() {
  const { user } = useAuth()
  const { pathname } = useLocation()
  if (!user) return null

  return (
    <Sidebar>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" render={<Link to="/dashboard" />}>
              <div className="bg-primary text-primary-foreground flex size-8 items-center justify-center rounded-lg">
                <HeartPulse className="size-5" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">SSC-ARC115</span>
                <span className="text-muted-foreground truncate text-xs">Salud comunitaria</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        {GROUPS.map((group) => {
          const items = group.items.filter((i) => i.roles.includes(user.role))
          if (items.length === 0) return null
          return (
            <SidebarGroup key={group.label}>
              <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
              <SidebarMenu>
                {items.map((item) => (
                  <SidebarMenuItem key={item.url}>
                    <SidebarMenuButton
                      tooltip={item.title}
                      isActive={pathname === item.url || pathname.startsWith(`${item.url}/`)}
                      render={<Link to={item.url} />}
                    >
                      <item.icon />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroup>
          )
        })}
      </SidebarContent>
      <SidebarFooter>
        <UserMenu />
      </SidebarFooter>
    </Sidebar>
  )
}
