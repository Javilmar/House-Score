/** Exportación CSV de Listados (app.py:1289-1308, 1470-1471). */
import type { Listing } from '../types'

export const COLUMNAS_CSV = [
  'title', 'price', 'score', 'eur_m2', 'location', 'm2', 'rooms', 'bathrooms',
  'floor', 'year_built', 'energy_rating', 'source', 'first_seen', 'url',
] as const satisfies readonly (keyof Listing)[]

export const nombreCsv = (hoy: string) => `listings_${hoy}.csv`

/** Escapado de pandas `to_csv` (QUOTE_MINIMAL). */
function celda(v: unknown): string {
  if (v === null || v === undefined) return ''
  const s = String(v)
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

export function generarCsv(listings: Listing[]): string {
  const filas = [COLUMNAS_CSV.join(',')]
  for (const l of listings) filas.push(COLUMNAS_CSV.map((c) => celda(l[c])).join(','))
  return filas.join('\n') + '\n'
}
