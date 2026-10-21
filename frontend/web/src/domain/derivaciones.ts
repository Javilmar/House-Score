/**
 * Derivaciones puras de un listing (app.py:340-426, 607-611, 1314-1320, 1372-1385).
 * Compartidas por Listados, Top scoring, Novedades y Bajadas.
 */
import { SCORE_SCALE } from '../styles/tema'
import type { Listing } from '../types'

export type Zona = 'Madrid Sur' | 'Toledo Norte' | '—'
export type Ccaa = 'Comunidad de Madrid' | 'Castilla-La Mancha'
export type TipoVivienda = 'Obra nueva' | 'Segunda mano'
type Texto = string | null | undefined

/** app.py:333-337 (incluye VS16 U+FE0F y ZWJ U+200D). */
const EMOJI_RE = /[\u{1f000}-\u{1faff}\u{2600}-\u{27bf}\u{1f1e6}-\u{1f1ff}\u{2190}-\u{21ff}\u{2b00}-\u{2bff}\u{fe0f}\u{200d}]/gu

/** `clean` (app.py:340): quita emojis y los espacios y "·" de los extremos. */
export function clean(text: string): string {
  return text.replace(EMOJI_RE, '').replace(/^[ ·]+|[ ·]+$/g, '')
}

/** `_sin_acentos` (app.py:383): NFKD sin marcas combinadas y en minúsculas. */
export function sinAcentos(s: string): string {
  return s.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase()
}

const MADRID_SUR = [
  'getafe', 'leganes', 'mostoles', 'alcorcon', 'fuenlabrada', 'parla', 'pinto', 'valdemoro',
  'ciempozuelos', 'humanes', 'grinon', 'navalcarnero', 'torrejon de la calzada',
  'cubas de la sagra', 'batres', 'serranillos del valle', 'moraleja de enmedio', 'arroyomolinos',
]
const TOLEDO_NORTE = ['illescas', 'senorio', 'sesena', 'quinon', 'yeles', 'ugena', 'esquivias']
const OBRA_NUEVA_KW = [
  'obra nueva', 'a estrenar', 'nueva construccion', 'primera ocupacion', 'de obra nueva',
  'promocion de obra', 'llave en mano', 'recien construid', 'vivienda nueva', 'promocion nueva',
]

const blob = (textos: Texto[]) => sinAcentos(textos.filter(Boolean).join(' '))

/** `zona` (app.py:388): Madrid Sur se evalúa antes que Toledo Norte; búsqueda por subcadena. */
export function zona(...textos: Texto[]): Zona {
  const b = blob(textos)
  if (MADRID_SUR.some((m) => b.includes(m))) return 'Madrid Sur'
  if (TOLEDO_NORTE.some((t) => b.includes(t))) return 'Toledo Norte'
  return '—'
}

/** `zona_a_ccaa` (app.py:398); CCAA_DEFAULT = Comunidad de Madrid. */
export function zonaACcaa(z: Zona): Ccaa {
  return z === 'Toledo Norte' ? 'Castilla-La Mancha' : 'Comunidad de Madrid'
}

/** Valor del parámetro `ccaa` de `#/hipoteca` (contracts/vistas.md). */
export function ccaaParam(z: Zona): 'madrid' | 'clm' {
  return zonaACcaa(z) === 'Castilla-La Mancha' ? 'clm' : 'madrid'
}

/** `tipo_vivienda` (app.py:421). */
export function tipoVivienda(...textos: Texto[]): TipoVivienda {
  const b = blob(textos)
  return OBRA_NUEVA_KW.some((kw) => b.includes(kw)) ? 'Obra nueva' : 'Segunda mano'
}

/** Valor del parámetro `tipo` de `#/hipoteca`. */
export function tipoParam(t: TipoVivienda): 'segunda-mano' | 'obra-nueva' {
  return t === 'Obra nueva' ? 'obra-nueva' : 'segunda-mano'
}

/** Zona y tipo de un listing con los mismos textos que app.py:1358-1365. */
export function zonaDe(l: Pick<Listing, 'location' | 'title' | 'description'>): Zona {
  return zona(l.location, l.title, l.description)
}
export function tipoDe(l: Pick<Listing, 'title' | 'description' | 'features'>): TipoVivienda {
  return tipoVivienda(l.title, l.description, Array.isArray(l.features) ? l.features.join(' ') : '')
}

/** `score_color` (app.py:607): primer umbral con `score >= umbral`; si ninguno, el último color. */
export function scoreColor(score: number): string {
  for (const [umbral, color] of SCORE_SCALE) if (score >= umbral) return color
  return SCORE_SCALE[SCORE_SCALE.length - 1]![1]
}

/** Redondeo half-to-even de Python (`round`). */
export function redondear(x: number): number {
  const f = Math.floor(x)
  const d = x - f
  if (d < 0.5) return f
  if (d > 0.5) return f + 1
  return f % 2 === 0 ? f : f + 1
}

/** Agrupa miles con `sep`; el signo se conserva. */
export function agruparMiles(entero: number, sep: string): string {
  const s = String(Math.abs(entero)).replace(/\B(?=(\d{3})+(?!\d))/g, sep)
  return entero < 0 ? `-${s}` : s
}

/** `_fmt_eur` (app.py:1314): miles con punto y " €"; nulo o no finito → "—". */
export function fmtEur(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return '—'
  return `${agruparMiles(redondear(v), '.')} €`
}

const aMs = (iso: string) => {
  const [a, m, d] = iso.split('-').map(Number) as [number, number, number]
  return Date.UTC(a, m - 1, d)
}

/** Días entre `first_seen` y hoy (ambos `yyyy-mm-dd`); sin fecha → null. */
export function diasEnMercado(firstSeen: string | null, hoy: string): number | null {
  if (!firstSeen) return null
  return Math.round((aMs(hoy) - aMs(firstSeen)) / 86_400_000)
}

/** Color del texto de "Días" (app.py:1379-1385). */
export function colorDias(dias: number | null): string {
  if (dias !== null && dias > 45) return '#f87171'
  if (dias !== null && dias > 20) return '#fbbf24'
  return '#a1a1aa'
}

/** Retirado ⇔ `status == "delisted"` (app.py:1348). */
export const esRetirado = (l: Pick<Listing, 'status'>): boolean => l.status === 'delisted'

/** `_muni` (app.py:1216): campo `municipio` en Title Case, o el texto entre paréntesis de `location`, o "—". */
export function municipioDe(l: Pick<Listing, 'municipio' | 'location'>): string {
  const m: unknown = l.municipio
  if (typeof m === 'string' && m.trim()) {
    return m.replace(/_/g, ' ').replace(/\p{L}+/gu, (w) => w[0]!.toUpperCase() + w.slice(1).toLowerCase())
  }
  const mm = /\(([^)]+)\)/.exec(String(l.location ?? ''))
  return mm ? mm[1]!.trim() : '—'
}
