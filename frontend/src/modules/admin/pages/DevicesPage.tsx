import { useState } from 'react'
import { useAuth } from '../../auth/hooks/useAuth'
import ApiKeyNotice from '../components/ApiKeyNotice'
import DeviceForm from '../components/DeviceForm'
import { useDevices } from '../hooks/useDevices'

export default function DevicesPage() {
  const { user } = useAuth()
  const canEdit = user?.role === 'admin'
  const { devices, loading, error, create, setActive, rotate } = useDevices()
  const [shown, setShown] = useState<{ id: string; key: string } | null>(null)
  const [actionError, setActionError] = useState('')

  async function run(action: () => Promise<void>) {
    setActionError('')
    try {
      await action()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'La acción falló.')
    }
  }

  const onRotate = (id: string) =>
    run(async () => {
      if (!window.confirm(`Se generará una clave nueva para ${id}. La anterior dejará de funcionar. ¿Continuar?`)) return
      setShown({ id, key: await rotate(id) })
    })

  return (
    <>
      <h1>Dispositivos</h1>
      {shown && <ApiKeyNotice deviceId={shown.id} apiKey={shown.key} onClose={() => setShown(null)} />}
      {canEdit && (
        <DeviceForm
          onCreate={async (data) => {
            setShown({ id: data.device_id, key: await create(data) })
          }}
        />
      )}
      {error && <p className="error">{error}</p>}
      {actionError && <p className="error">{actionError}</p>}
      {loading ? (
        <p>Cargando…</p>
      ) : devices.length === 0 ? (
        <p>No hay dispositivos registrados.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Identificador</th>
              <th>Nombre</th>
              <th>Promotor</th>
              <th>Estado</th>
              {canEdit && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.device_id}>
                <td>{d.device_id}</td>
                <td>{d.name}</td>
                <td>{d.promoter_email}</td>
                <td>{d.active ? 'Activo' : 'Desactivado'}</td>
                {canEdit && (
                  <td className="row">
                    <button type="button" className="secondary" onClick={() => run(() => setActive(d.device_id, !d.active))}>
                      {d.active ? 'Desactivar' : 'Activar'}
                    </button>
                    <button type="button" className="secondary" onClick={() => onRotate(d.device_id)}>
                      Nueva clave
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}
