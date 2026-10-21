import { Moon, Sun } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { applyTheme, getStoredTheme } from '@/lib/theme'
import type { Theme } from '@/lib/theme'

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(getStoredTheme)

  function toggle() {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    applyTheme(next)
    setTheme(next)
  }

  return (
    <Button variant="ghost" size="icon" onClick={toggle} aria-label="Cambiar entre tema claro y oscuro">
      {theme === 'dark' ? <Sun /> : <Moon />}
    </Button>
  )
}
