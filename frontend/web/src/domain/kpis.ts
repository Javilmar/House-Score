/** KPI de la cabecera (app.py:987-1035). */
import { agruparMiles, esRetirado, redondear } from './derivaciones'
import type { Listing } from '../types'

export interface Kpi {
  icono: string
  etiqueta: string
  valor: string
}

const media = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length

export function calcularKpis(todos: Listing[], hoy: string): Kpi[] {
  const activos = todos.filter((l) => !esRetirado(l))
  const nuevosHoy = activos.filter((l) => l.first_seen === hoy)
  const bajadas = activos.filter((l) => l.price_drop !== null && l.price_drop > 0)
  const sinValorar = activos.filter((l) => l.datos_insuficientes)
  const fiables = activos.filter((l) => !l.datos_insuficientes)
  const scoreSrc = fiables.length > 0 ? fiables : activos
  const hay = activos.length > 0

  return [
    { icono: 'layers', etiqueta: 'Total listings', valor: String(activos.length) },
    { icono: 'sparkles', etiqueta: 'Nuevos hoy', valor: String(nuevosHoy.length) },
    {
      icono: 'star',
      etiqueta: 'Score medio',
      valor: hay ? media(scoreSrc.map((l) => l.score)).toFixed(1) : '—',
    },
    {
      icono: 'wallet',
      etiqueta: 'Precio medio',
      valor: hay ? `${agruparMiles(redondear(media(activos.map((l) => l.price))), ',')} €` : '—',
    },
    { icono: 'trending-down', etiqueta: 'Bajadas', valor: String(bajadas.length) },
    { icono: 'ruler', etiqueta: 'Sin valorar', valor: String(sinValorar.length) },
  ]
}
