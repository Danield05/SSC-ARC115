import type { Patient } from '../types'

/** Minúsculas y sin tildes: «José» y «jose» se encuentran entre sí. */
export const normalize = (text: string) =>
  text
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .toLowerCase()
    .trim()

/**
 * Cada palabra escrita tiene que aparecer en el nombre completo (nombres y apellidos) o en el
 * código (`P-0003`, `P0003` o solo `0003`). Sin texto, entran todos.
 * «juan» trae a todos los Juan, «orellana» a todos con ese apellido.
 */
export function matchesPatient(patient: Pick<Patient, 'name' | 'patient_code'>, query: string): boolean {
  const words = normalize(query).split(/\s+/).filter(Boolean)
  if (words.length === 0) return true
  const code = normalize(patient.patient_code)
  const haystack = `${normalize(patient.name)} ${code} ${code.replaceAll('-', '')}`
  return words.every((word) => haystack.includes(word))
}
