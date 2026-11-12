/**
 * Aviso dentro de la página de que llegó una medición nueva (la orden «Medir» se completó). Las
 * pantallas que muestran el historial lo escuchan y vuelven a pedir sus datos.
 */
const EVENT = 'ssc:measurement-received'

export const notifyMeasurementReceived = () => window.dispatchEvent(new Event(EVENT))

export function onMeasurementReceived(listener: () => void) {
  window.addEventListener(EVENT, listener)
  return () => window.removeEventListener(EVENT, listener)
}
