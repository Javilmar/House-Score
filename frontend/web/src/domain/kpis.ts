/** KPI de la cabecera (app.py:987-1035). */
import { agruparMiles, redondear } from './derivaciones'
import type { Listing } from '../types'

export interface Kpi {
  icono: string
  etiqueta: string
  valor: string
}

const media = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length

export function calcularKpis(listings: Listing[], hoy: string): Kpi[] {
  const activos = listings.filter((l) => l.status === 'active')
  const nuevosHoy = listings.filter((l) => l.first_seen === hoy)
  const bajadas = listings.filter((l) => l.price_drop !== null && l.price_drop > 0)
  const sinValorar = listings.filter((l) => l.datos_insuficientes)
  const fiables = listings.filter((l) => !l.datos_insuficientes)
  const scoreSrc = fiables.length > 0 ? fiables : listings
  const hay = listings.length > 0

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
      valor: hay ? `${agruparMiles(redondear(media(listings.map((l) => l.price))), ',')} €` : '—',
    },
    { icono: 'trending-down', etiqueta: 'Bajadas', valor: String(bajadas.length) },
    { icono: 'ruler', etiqueta: 'Sin valorar', valor: String(sinValorar.length) },
  ]
}
