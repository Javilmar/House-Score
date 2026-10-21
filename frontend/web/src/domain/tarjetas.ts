/**
 * Lógica pura de las tarjetas de Top scoring, Novedades y Bajadas (app.py:1473-1935).
 * La vista solo pinta lo que devuelven estas funciones.
 */
import type { ParamsEntrada } from '../state/router'
import type { Listing } from '../types'
import {
  agruparMiles,
  ccaaParam,
  clean,
  diasEnMercado,
  redondear,
  tipoParam,
  tipoVivienda,
  zona,
  type TipoVivienda,
  type Zona,
} from './derivaciones'

export const TOP_MIN = 5
export const TOP_MAX = 30
export const TOP_DEFECTO = 15
/** Longitud máxima de la descripción de la tarjeta (app.py:1533). */
export const DESCRIPCION_MAX = 1500

/** Parámetros de `#/hipoteca` para un precio, tipo y zona (contracts/vistas.md). */
export function paramsHipoteca(precio: number, tipo: TipoVivienda, z: Zona): ParamsEntrada {
  return { precio: Math.trunc(Number.isFinite(precio) ? precio : 0), tipo: tipoParam(tipo), ccaa: ccaaParam(z) }
}

/**
 * Parámetros del botón € Hipoteca de las tarjetas (app.py:1524-1529): el tipo se deduce
 * solo de título y descripción (a diferencia de la tabla de Listados, que añade las características).
 */
export function paramsHipotecaTarjeta(l: Pick<Listing, 'price' | 'title' | 'description' | 'location'>): ParamsEntrada {
  return paramsHipoteca(l.price, tipoVivienda(l.title, l.description, ''), zona(l.location, l.title, l.description))
}

/** Formato de Python `{:,.0f}`: miles con coma, redondeo half-to-even. */
export function fmtComa(v: number): string {
  return agruparMiles(redondear(Number.isFinite(v) ? v : 0), ',')
}

/** Formato de `f"{int(v):,}".replace(",", ".")` (Novedades). */
export function fmtPunto(v: number): string {
  return agruparMiles(Math.trunc(v), '.')
}

/** Parámetro `n` de Top: entero acotado a 5–30; ausente o ilegible → 15. */
export function topNDeParam(v: string | string[] | undefined): number {
  const t = Array.isArray(v) ? v[0] : v
  const n = Number.parseInt(t ?? '', 10)
  return Number.isFinite(n) ? Math.min(TOP_MAX, Math.max(TOP_MIN, n)) : TOP_DEFECTO
}

/** Texto de la descripción: truncado a 1500 y limpio; vacío si no supera 20 caracteres (app.py:1531-1534). */
export function descripcionTarjeta(descripcion: string | null | undefined): string {
  if (typeof descripcion !== 'string') return ''
  const letras = Array.from(descripcion)
  return letras.length > 20 ? clean(letras.slice(0, DESCRIPCION_MAX).join('')) : ''
}

/** Valor del campo de meta: `clean(str(val)) or "—"`. */
export const metaValor = (v: unknown): string => clean(String(v ?? '')) || '—'

/** Líneas de meta de Top (app.py:1496-1501): icono y texto. */
export function metaTop(l: Listing): [icono: string, texto: string][] {
  return [
    ['map-pin', metaValor(l.location === '' ? '—' : l.location)],
    ['building', metaValor(`Planta ${l.floor}`)],
    ['calendar', metaValor(l.year_built)],
    ['zap', metaValor(l.energy_rating === '' ? '—' : l.energy_rating)],
  ]
}

// ── ordenación ────────────────────────────────────────────────────────────

type Clave = number | string | null

/** `sort_values(col, ascending, na_position="last")`; estable. */
function ordenarPor<T>(xs: T[], clave: (x: T) => Clave, asc: boolean): T[] {
  const esNulo = (c: Clave) => c === null || (typeof c === 'number' && !Number.isFinite(c))
  return xs
    .map((x, i) => ({ x, i, c: clave(x) }))
    .sort((a, b) => {
      const na = esNulo(a.c)
      const nb = esNulo(b.c)
      if (na || nb) return na === nb ? a.i - b.i : na ? 1 : -1
      const d = a.c! < b.c! ? -1 : a.c! > b.c! ? 1 : 0
      return d === 0 ? a.i - b.i : asc ? d : -d
    })
    .map((e) => e.x)
}

// ── Bajadas de precio ─────────────────────────────────────────────────────

export const ORDENES_BAJADAS = [
  'Mayor bajada (€)',
  'Mayor bajada (%)',
  'Mejor score',
  'Precio más bajo',
  'Más reciente',
] as const
export type OrdenBajadas = (typeof ORDENES_BAJADAS)[number]
export const ORDEN_BAJADAS_DEFECTO: OrdenBajadas = ORDENES_BAJADAS[0]

/** `price_drop` notna y > 0 (app.py:994-998). */
export const hayBajada = (l: Pick<Listing, 'price_drop'>): boolean =>
  l.price_drop !== null && Number.isFinite(l.price_drop) && l.price_drop > 0

export function ordenBajadasDeParam(v: string | string[] | undefined): OrdenBajadas {
  const t = Array.isArray(v) ? v[0] : v
  return (ORDENES_BAJADAS as readonly string[]).includes(t ?? '') ? (t as OrdenBajadas) : ORDEN_BAJADAS_DEFECTO
}

/** `_pct_drop` solo para ordenar (app.py:1717-1722): drop / (precio + drop) · 100. */
const pctOrden = (l: Listing) => (l.price_drop! / (l.price + l.price_drop!)) * 100

export function ordenarBajadas(listings: Listing[], orden: OrdenBajadas): Listing[] {
  const bajadas = listings.filter(hayBajada)
  switch (orden) {
    case 'Mayor bajada (€)':
      return ordenarPor(bajadas, (l) => l.price_drop, false)
    case 'Mayor bajada (%)':
      return ordenarPor(bajadas, pctOrden, false)
    case 'Mejor score':
      return ordenarPor(bajadas, (l) => l.score, false)
    case 'Precio más bajo':
      return ordenarPor(bajadas, (l) => l.price, true)
    case 'Más reciente':
      return ordenarPor(bajadas, (l) => l.first_seen, false)
  }
}

export interface PreciosBajada {
  actual: number
  /** Precio anterior; si falta se reconstruye como actual + bajada (app.py:1750). */
  previo: number
  /** Bajada en % del precio anterior, 0 si el anterior es 0 (app.py:1751). */
  pct: number
}

export function preciosBajada(l: Pick<Listing, 'price' | 'price_drop' | 'previous_price'>): PreciosBajada {
  const actual = Number.isFinite(l.price) ? l.price : 0
  const bajada = l.price_drop !== null && Number.isFinite(l.price_drop) ? l.price_drop : 0
  const previo = l.previous_price !== null && Number.isFinite(l.previous_price) ? l.previous_price : actual + bajada
  return { actual, previo, pct: previo ? (bajada / previo) * 100 : 0 }
}

/** Meta de una bajada: ubicación · fuente [· Nd en mercado] (app.py:1740-1773). */
export function metaBajada(l: Listing, hoy: string): string {
  const base = [l.location === '' ? '—' : l.location, l.source === '' ? '—' : l.source]
    .map((p) => clean(String(p)) || '—')
    .join(' · ')
  const dias = diasEnMercado(l.first_seen, hoy)
  return dias === null ? base : `${base} · ${dias}d en mercado`
}

// ── Novedades ─────────────────────────────────────────────────────────────

export const ORDENES_NOVEDADES = ['Mejor score', 'Precio más bajo', 'Mayor superficie', 'Más antiguo'] as const
export type OrdenNovedades = (typeof ORDENES_NOVEDADES)[number]
export const ORDEN_NOVEDADES_DEFECTO: OrdenNovedades = ORDENES_NOVEDADES[0]

/** Fechas con pisos nuevos (`first_seen` distintas), la más reciente primero (app.py:1813). */
export function fechasNovedades(listings: Listing[]): string[] {
  const fechas = new Set<string>()
  for (const l of listings) if (l.first_seen) fechas.add(l.first_seen)
  return [...fechas].sort().reverse()
}

/** Los listings que aparecieron por primera vez en `fecha`, ordenados (app.py:1828-1842). */
export function nuevosDe(listings: Listing[], fecha: string, orden: OrdenNovedades): Listing[] {
  const nuevos = listings.filter((l) => l.first_seen === fecha)
  switch (orden) {
    case 'Mejor score':
      return ordenarPor(nuevos, (l) => l.score, false)
    case 'Precio más bajo':
      return ordenarPor(nuevos, (l) => l.price, true)
    case 'Mayor superficie':
      return ordenarPor(nuevos, (l) => l.m2, false)
    case 'Más antiguo':
      return ordenarPor(nuevos, (l) => l.first_seen, true)
  }
}

/** Precio, detalles y meta de una tarjeta de Novedades (app.py:1871-1895). */
export function textosNovedad(l: Listing): { meta: string; detalles: string; precio: string } {
  const loc = clean(String(l.location === '' ? '—' : l.location)) || '—'
  const src = clean(String(l.source ?? '')) || ''
  const num = (v: number | null) => v !== null && Number.isFinite(v)
  return {
    meta: [loc, src].filter(Boolean).join(' · '),
    detalles: [
      num(l.m2) ? `${Math.trunc(l.m2)} m²` : '',
      num(l.eur_m2) ? `${fmtPunto(l.eur_m2!)} €/m²` : '',
      num(l.rooms) ? `${Math.trunc(l.rooms)} hab` : '',
    ]
      .filter(Boolean)
      .join(' · '),
    precio: num(l.price) ? `${fmtPunto(l.price)} €` : '—',
  }
}
