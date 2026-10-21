/**
 * Filtros combinativos y ordenación de Listados (app.py:1204-1312 y JS `ord`, app.py:522-545).
 * Todo es puro: la vista guarda el estado en el hash y llama a estas funciones.
 */
import { comoLista, type ParamsEntrada, type ParamsRuta } from '../state/router'
import type { Listing } from '../types'
import {
  clean,
  diasEnMercado,
  esRetirado,
  municipioDe,
  redondear,
  tipoDe,
  zonaDe,
  type TipoVivienda,
  type Zona,
} from './derivaciones'

export type Rango = [number, number]

/** Listing con las columnas derivadas que usan filtros, tabla y botones. */
export interface Fila {
  l: Listing
  zona: Zona
  municipio: string
  tipo: TipoVivienda
  /** Posición en el orden de entrada (score descendente): destino del botón ↗. */
  rank: number
}

export interface Filtros {
  retirados: boolean
  zonas: string[]
  municipios: string[]
  score: Rango
  /** null = sin datos de precio (no se filtra) */
  precio: Rango | null
  /** null = sin recorrido (min == max) o sin datos: no se filtra */
  hab: Rango | null
}

/** Opciones y límites de los controles, calculados sobre la base (no sobre el resultado). */
export interface Opciones {
  zonas: string[]
  municipios: string[]
  score: Rango
  precio: Rango | null
  hab: Rango | null
}

export const SCORE_RANGO: Rango = [0, 100]
const ZONAS_ORDEN: Zona[] = ['Madrid Sur', 'Toledo Norte']

export function enriquecer(listings: Listing[]): Fila[] {
  return listings.map((l, rank) => ({ l, zona: zonaDe(l), municipio: municipioDe(l), tipo: tipoDe(l), rank }))
}

const rangoDe = (xs: number[]): Rango | null => {
  if (xs.length === 0) return null
  let min = xs[0]!
  let max = xs[0]!
  for (const x of xs) {
    if (x < min) min = x
    if (x > max) max = x
  }
  return [Math.trunc(min), Math.trunc(max)]
}

/** `base` (app.py:1205): sin retirados salvo que se pidan. */
export const filasBase = (filas: Fila[], retirados: boolean): Fila[] =>
  retirados ? filas : filas.filter((f) => !esRetirado(f.l))

function opcionesDe(base: Fila[], zonasSel: string[]): Opciones {
  const presentes = new Set<string>(base.map((f) => f.zona))
  const pool = zonasSel.length > 0 ? base.filter((f) => zonasSel.includes(f.zona)) : base
  const municipios = [...new Set(pool.map((f) => f.municipio))]
    .filter((m) => m && m !== '—')
    .sort((a, b) => (a < b ? -1 : a > b ? 1 : 0)) // sorted() de Python: por punto de código
  const hab = rangoDe(base.map((f) => f.l.rooms))
  return {
    zonas: ZONAS_ORDEN.filter((z) => presentes.has(z)),
    municipios,
    score: SCORE_RANGO,
    precio: rangoDe(base.map((f) => f.l.price)),
    hab: hab && hab[0] < hab[1] ? hab : null,
  }
}

function leerRango(texto: string | string[] | undefined, limites: Rango): Rango {
  const m = /^(-?\d+)-(-?\d+)$/.exec(Array.isArray(texto) ? (texto[0] ?? '') : (texto ?? ''))
  if (!m) return limites
  const acota = (n: number) => Math.min(limites[1], Math.max(limites[0], n))
  const a = acota(Number(m[1]))
  const b = acota(Number(m[2]))
  return a <= b ? [a, b] : limites
}

/**
 * Del hash a los filtros efectivos: base, selección saneada (solo valores que existen en las
 * opciones vigentes, p. ej. un municipio fuera de la zona elegida se descarta) y rangos acotados.
 */
export function resolverFiltros(
  filas: Fila[],
  params: ParamsRuta,
): { base: Fila[]; filtros: Filtros; opciones: Opciones } {
  const retirados = params['retirados'] === '1'
  const base = filasBase(filas, retirados)
  const zonasDisp = opcionesDe(base, []).zonas
  const zonas = comoLista(params['zona']).filter((z) => zonasDisp.includes(z))
  const opciones = opcionesDe(base, zonas)
  const municipios = comoLista(params['muni']).filter((m) => opciones.municipios.includes(m))
  const filtros: Filtros = {
    retirados,
    zonas,
    municipios,
    score: leerRango(params['score'], opciones.score),
    precio: opciones.precio && leerRango(params['precio'], opciones.precio),
    hab: opciones.hab && leerRango(params['hab'], opciones.hab),
  }
  return { base, filtros, opciones }
}

const igual = (a: Rango, b: Rango) => a[0] === b[0] && a[1] === b[1]
const texto = (r: Rango) => `${r[0]}-${r[1]}`

/** De los filtros al hash: solo lo que difiere de los valores por defecto. */
export function paramsDeFiltros(f: Filtros, op: Opciones): ParamsEntrada {
  const p: ParamsEntrada = {}
  if (f.zonas.length) p['zona'] = f.zonas
  if (f.municipios.length) p['muni'] = f.municipios
  if (!igual(f.score, op.score)) p['score'] = texto(f.score)
  if (f.precio && op.precio && !igual(f.precio, op.precio)) p['precio'] = texto(f.precio)
  if (f.hab && op.hab && !igual(f.hab, op.hab)) p['hab'] = texto(f.hab)
  if (f.retirados) p['retirados'] = '1'
  return p
}

const dentro = (v: number, r: Rango) => v >= r[0] && v <= r[1]

/** Orden de aplicación de app.py:1268-1287; resultado por score descendente (estable). */
export function aplicarFiltros(base: Fila[], f: Filtros): Fila[] {
  const out = base.filter(
    (x) =>
      (f.zonas.length === 0 || f.zonas.includes(x.zona)) &&
      (f.municipios.length === 0 || f.municipios.includes(x.municipio)) &&
      dentro(x.l.score, f.score) &&
      (!f.precio || dentro(x.l.price, f.precio)) &&
      (!f.hab || dentro(x.l.rooms, f.hab)),
  )
  return out.sort((a, b) => b.l.score - a.l.score)
}

export type Columna = 'titulo' | 'precio' | 'score' | 'eur_m2' | 'm2' | 'tipo' | 'fuente' | 'ubicacion' | 'dias'
export type Direccion = 'asc' | 'desc'

export const tituloDe = (l: Pick<Listing, 'title'>): string => clean(String(l.title ?? '')) || 'Sin título'
const num = (v: number | null) => (v !== null && Number.isFinite(v) ? v : '')
export const scoreFinito = (l: Pick<Listing, 'score'>): number => (Number.isFinite(l.score) ? l.score : 0)
export const fuenteDe = (l: Pick<Listing, 'source'>): string => String(l.source ?? '').trim().toLowerCase()

/** Valor de ordenación de una celda (el `data-v` del original): número o texto ('' = vacío). */
export function valorOrden(f: Fila, col: Columna, hoy: string): number | string {
  const l = f.l
  switch (col) {
    case 'titulo':
      return tituloDe(l).toLowerCase()
    case 'precio':
      return num(l.price)
    case 'score':
      return redondear(scoreFinito(l))
    case 'eur_m2':
      return num(l.eur_m2)
    case 'm2':
      return num(l.m2)
    case 'tipo':
      return f.tipo
    case 'fuente':
      return fuenteDe(l)
    case 'ubicacion':
      return f.zona
    case 'dias':
      return diasEnMercado(l.first_seen, hoy) ?? 9999
  }
}

const colador = new Intl.Collator('es', { sensitivity: 'base' })

/** Comparador de `ord()`: números primero, luego texto con localeCompare('es', base). */
function comparar(x: number | string, y: number | string): number {
  const xn = typeof x === 'number'
  const yn = typeof y === 'number'
  if (xn && yn) return x - y
  if (xn) return -1
  if (yn) return 1
  return colador.compare(x, y)
}

/** Ordena sin mutar; estable. En descendente el comparador se invierte, como en el original. */
export function ordenar<T extends Fila>(filas: T[], col: Columna, dir: Direccion, hoy: string): T[] {
  const signo = dir === 'asc' ? 1 : -1
  return filas
    .map((fila) => ({ fila, clave: valorOrden(fila, col, hoy) }))
    .sort((a, b) => signo * comparar(a.clave, b.clave))
    .map((x) => x.fila)
}
