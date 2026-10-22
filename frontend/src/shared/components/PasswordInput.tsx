import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'
import type { ComponentProps } from 'react'
import { Input } from '@/components/ui/input'

/** Campo de contraseña con un ojito para mostrarla u ocultarla. */
export default function PasswordInput(props: Omit<ComponentProps<'input'>, 'type'>) {
  const [visible, setVisible] = useState(false)
  const label = visible ? 'Ocultar contraseña' : 'Mostrar contraseña'

  return (
    <div className="relative">
      <Input {...props} type={visible ? 'text' : 'password'} className="pr-10" />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={label}
        title={label}
        aria-pressed={visible}
        className="text-muted-foreground hover:text-foreground absolute inset-y-0 right-0 flex w-10 cursor-pointer items-center justify-center rounded-r-md outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
      >
        {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
      </button>
    </div>
  )
}
