import { useEffect, useState } from 'react'

const ZONE = 'America/El_Salvador'
const timeFormat = new Intl.DateTimeFormat('es-SV', {
  timeZone: ZONE,
  hour: 'numeric',
  minute: '2-digit',
  second: '2-digit',
  hour12: true,
})
const dateFormat = new Intl.DateTimeFormat('es-SV', {
  timeZone: ZONE,
  weekday: 'short',
  day: 'numeric',
  month: 'short',
})

/**
 * Reloj de la barra superior, con la hora de El Salvador (UTC−6): la misma con la que el historial
 * y los archivos exportados muestran las mediciones. Se actualiza cada segundo.
 */
export default function Clock() {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <time
      dateTime={now.toISOString()}
      title="Hora de El Salvador"
      className="text-muted-foreground flex items-center gap-2 text-sm tabular-nums"
    >
      <span className="hidden capitalize md:inline">{dateFormat.format(now)}</span>
      <span className="text-foreground font-medium">{timeFormat.format(now)}</span>
    </time>
  )
}
