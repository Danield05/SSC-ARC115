import { Activity, Scale, Thermometer } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/** Umbrales de alerta del servidor (backend/app/core/config.py). */
export interface AlertThresholds {
  temp_low_c: number
  temp_high_c: number
  spo2_min: number
}

/**
 * Valores por defecto del servidor (TEMP_LOW_C, TEMP_HIGH_C y SPO2_MIN en backend/template.yaml).
 * El Resumen no los pide a la API; si el servidor los cambia, hay que cambiarlos aquí. El historial
 * del paciente sí recibe los reales y se los pasa a la ventana de información.
 */
export const DEFAULT_THRESHOLDS: AlertThresholds = { temp_low_c: 35, temp_high_c: 38, spo2_min: 92 }

export type VitalKey = 'weight' | 'temperature' | 'spo2'

/** Orden en que se muestran las tarjetas. */
export const VITAL_KEYS: VitalKey[] = ['weight', 'temperature', 'spo2']

export const DISCLAIMER = 'Información orientativa. Este sistema registra y da seguimiento; no emite diagnósticos médicos.'

export interface VitalInfo {
  /** Título de la tarjeta. */
  title: string
  /** Título de la ventana. */
  dialogTitle: string
  icon: LucideIcon
  /** Texto corto de la tarjeta. */
  summary: string
  /** Etiqueta de la tarjeta: en rojo si es una alerta, neutra si es solo seguimiento. */
  badge: { text: string; alert: boolean }
  /** Primer párrafo de la ventana. */
  intro: string
  /** Cómo lo mide el dispositivo. */
  how: string
  reference: { rows: { label: string; value: string }[]; note: string }
  alert: { badge: string; alert: boolean; text: string }
  /** «Qué puede indicar», «Qué hacer» y «Tenlo en cuenta». */
  sections: { title: string; text: string }[]
  sources: string[]
}

/** Textos de las tarjetas y de las ventanas «Más información». Los umbrales salen de `t`. */
export function getVitalInfo(key: VitalKey, t: AlertThresholds = DEFAULT_THRESHOLDS): VitalInfo {
  switch (key) {
    case 'weight':
      return {
        title: 'Peso',
        dialogTitle: 'Peso e IMC',
        icon: Scale,
        summary:
          'Junto con la estatura se calcula el IMC. El exceso de peso aumenta el riesgo de diabetes tipo 2, hipertensión y enfermedades del corazón; el bajo peso puede indicar desnutrición.',
        badge: { text: 'Solo seguimiento', alert: false },
        intro:
          'Tu peso en kilogramos. Junto con la estatura que se registra en la app se calcula el IMC (peso dividido entre la estatura al cuadrado).',
        how: 'Plataforma con cuatro celdas de carga y un módulo HX711.',
        reference: {
          rows: [
            { label: 'Bajo peso', value: 'Menos de 18.5' },
            { label: 'Rango habitual', value: '18.5 a 24.9' },
            { label: 'Sobrepeso', value: '25 o más' },
            { label: 'Obesidad', value: '30 o más' },
          ],
          note: 'Para adultos. En menores de 18 años el IMC se interpreta según la edad y el sexo.',
        },
        alert: {
          badge: 'Sin alerta',
          alert: false,
          text: 'El peso es solo de seguimiento; se compara con las mediciones anteriores.',
        },
        sections: [
          {
            title: 'Qué puede indicar',
            text: 'Un IMC alto aumenta el riesgo de enfermedades del corazón, diabetes, problemas de las articulaciones y algunos tipos de cáncer. Un peso muy bajo puede indicar mala nutrición u otro problema de salud.',
          },
          {
            title: 'Qué hacer',
            text: 'Medir con la misma báscula y a la misma hora ayuda a ver la tendencia. Si el IMC está fuera del rango habitual, conviene consultar a un profesional de salud.',
          },
          {
            title: 'Tenlo en cuenta',
            text: 'El IMC no distingue entre músculo y grasa, así que es una guía y no un diagnóstico.',
          },
        ],
        sources: ['Organización Mundial de la Salud. Obesidad y sobrepeso (datos y cifras)'],
      }
    case 'temperature':
      return {
        title: 'Temperatura',
        dialogTitle: 'Temperatura corporal',
        icon: Thermometer,
        summary:
          'Una temperatura alta suele acompañar infecciones o inflamación. Una temperatura muy baja puede indicar hipotermia.',
        badge: { text: `Alerta: ${t.temp_low_c} °C o menos, ${t.temp_high_c} °C o más`, alert: true },
        intro: 'La temperatura del cuerpo en grados Celsius.',
        how: 'Sensor infrarrojo MLX90614, sin contacto con la piel.',
        reference: {
          rows: [
            { label: 'Alerta baja', value: `${t.temp_low_c} °C o menos` },
            { label: 'Sin alerta', value: `Más de ${t.temp_low_c} °C y menos de ${t.temp_high_c} °C` },
            { label: 'Alerta alta (fiebre)', value: `${t.temp_high_c} °C o más` },
          ],
          note: 'Estos son los umbrales que usa el sistema para avisar por correo.',
        },
        alert: {
          badge: 'Alerta por correo',
          alert: true,
          text: 'Si la medición cae en una alerta, se avisa al responsable.',
        },
        sections: [
          {
            title: 'Qué puede indicar',
            text: 'Una temperatura alta suele acompañar infecciones u otras enfermedades. Una temperatura muy baja puede indicar que el cuerpo está perdiendo calor.',
          },
          {
            title: 'Qué hacer',
            text: 'Repetir la medición pasados unos minutos, lejos de sol directo o corrientes de aire. Si la fiebre dura más de 3 o 4 días, o aparecen otros síntomas, consultar a un médico.',
          },
          {
            title: 'Tenlo en cuenta',
            text: 'Los termómetros infrarrojos sin contacto pueden dar valores distintos a los de referencia.',
          },
        ],
        sources: [
          'Clínica Mayo. Fiebre: primeros auxilios',
          'Manual MSD. Fiebre en adultos',
          'Sullivan et al. (2021). Scientific Reports, 11, 22079',
        ],
      }
    case 'spo2':
      return {
        title: 'Oxigenación (SpO₂)',
        dialogTitle: 'Oxigenación (SpO₂)',
        icon: Activity,
        summary:
          'Un nivel bajo de oxígeno puede asociarse a problemas respiratorios o del corazón, como neumonía, asma o EPOC.',
        badge: { text: `Alerta: menos de ${t.spo2_min} %`, alert: true },
        intro: 'El porcentaje de hemoglobina de la sangre que lleva oxígeno.',
        how: 'Sensor MAX30102, colocando el dedo sobre él. También entrega el pulso en latidos por minuto.',
        reference: {
          rows: [
            { label: 'Alerta', value: `Menos de ${t.spo2_min} %` },
            { label: 'Sin alerta', value: `${t.spo2_min} % o más` },
          ],
          note: 'Umbral que usa el sistema para avisar por correo.',
        },
        alert: {
          badge: 'Alerta por correo',
          alert: true,
          text: 'Si la medición cae por debajo del umbral, se avisa al responsable.',
        },
        sections: [
          {
            title: 'Qué puede indicar',
            text: 'Valores bajos pueden asociarse a problemas respiratorios o del corazón, como neumonía, asma o EPOC.',
          },
          {
            title: 'Qué hacer',
            text: 'Repetir con la mano quieta y tibia. Si sigue baja, o hay falta de aire, dolor de pecho, confusión o labios azulados, buscar atención médica de inmediato.',
          },
          {
            title: 'Tenlo en cuenta',
            text: 'Los oxímetros pueden variar alrededor de 2 puntos y son menos precisos con piel muy oscura o niveles muy bajos de oxígeno.',
          },
        ],
        sources: ['American Thoracic Society. Oximetría de pulso (guía para pacientes)'],
      }
  }
}
