/**
 * Mapas (app.py:2348-2714, `with tab8:`). Constructores puros de los coropletas
 * (equivalentes a `px.choropleth_map`), join de assets y rankings.
 */
import type { Listing } from '../types'
import { BORDER, INK, MUTED, SURFACE } from '../styles/tema'

export interface GeoFeature {
  type: string
  properties: Record<string, string | number | null>
  geometry: unknown
}
export interface GeoJson {
  type: string
  features: GeoFeature[]
}

export interface FilaCriminalidad {
  cod_ine: string
  municipio: string
  tasa_criminalidad: number
  periodo: string
}

export interface FilaSeccion {
  cusec: string
  cod_ine: string
  municipio: string
  renta_persona: number | null
  anio: string
}

export interface FilaPrecio {
  municipio: string
  cod_ine: string
  nombre: string
  eur_m2_med: number
  precio_med: number
  n_listings: number
}

export interface Figura {
  data: unknown[]
  layout: Record<string, unknown>
}

export type CapaId = 'criminalidad' | 'renta' | 'precio'

// ── Constantes (app.py:2395-2441, 2642) ─────────────────────────────────────

export type Escala = [number, string][]

export const COLOR_CRIMINALIDAD: Escala = [
  [0.0, '#22c55e'],
  [0.35, '#84cc16'],
  [0.55, '#eab308'],
  [0.75, '#f97316'],
  [1.0, '#ef4444'],
]
export const COLOR_RENTA: Escala = [
  [0.0, '#ef4444'],
  [0.25, '#f97316'],
  [0.5, '#eab308'],
  [0.75, '#84cc16'],
  [1.0, '#22c55e'],
]
export const COLOR_PRECIO: Escala = COLOR_CRIMINALIDAD.map(([n, c]) => [n, c])

export const CENTRO = { lat: 40.18, lon: -3.78 }
const ESTILO = 'carto-darkmatter'
const OPACIDAD = 0.75
const TRANSPARENTE = 'rgba(0,0,0,0)'

const LAYOUT_MAPA = {
  paper_bgcolor: TRANSPARENTE,
  plot_bgcolor: TRANSPARENTE,
  margin: { l: 0, r: 0, t: 0, b: 48 },
  height: 540,
  font: { family: 'Inter', size: 12, color: MUTED },
  hoverlabel: { bgcolor: SURFACE, bordercolor: BORDER, font: { family: 'Inter', color: INK } },
}

const colorbar = (titulo: string) => ({
  orientation: 'h',
  x: 0.5,
  xanchor: 'center',
  y: -0.04,
  yanchor: 'top',
  thickness: 10,
  len: 0.72,
  title: { text: titulo, side: 'top', font: { color: MUTED, size: 11 } },
  tickfont: { color: MUTED, size: 10 },
  bgcolor: TRANSPARENTE,
  bordercolor: BORDER,
})

// ── Capas (app.py:2377-2392) ────────────────────────────────────────────────

const ETIQUETAS: Record<CapaId, string> = {
  criminalidad: '🔴  Criminalidad · por municipio',
  renta: '🟢  Renta · por barrio (sección censal)',
  precio: '🟡  Precio vivienda · por municipio',
}

export function capasDisponibles(tieneCriminalidad: boolean, tieneRenta: boolean): { id: CapaId; etiqueta: string }[] {
  const ids: CapaId[] = []
  if (tieneCriminalidad) ids.push('criminalidad')
  if (tieneRenta) ids.push('renta')
  ids.push('precio')
  return ids.map((id) => ({ id, etiqueta: ETIQUETAS[id] }))
}

/** Capa elegida por el parámetro de ruta, o la primera disponible (índice 0 del radio). */
export function capaActiva(capas: { id: CapaId }[], param: string | string[] | undefined): CapaId {
  const p = Array.isArray(param) ? param[0] : param
  return capas.find((c) => c.id === p)?.id ?? capas[0]!.id
}

// ── Carga de assets (app.py:564-604) ────────────────────────────────────────

function filasCsv(texto: string): string[][] {
  const lineas = texto.split(/\r?\n/).filter((l) => l.trim() !== '' && !l.startsWith('#'))
  return lineas.map((linea) => {
    const campos: string[] = []
    let actual = ''
    let entrecomillado = false
    for (let i = 0; i < linea.length; i++) {
      const c = linea[i]!
      if (entrecomillado) {
        if (c === '"' && linea[i + 1] === '"') {
          actual += '"'
          i++
        } else if (c === '"') entrecomillado = false
        else actual += c
      } else if (c === '"') entrecomillado = true
      else if (c === ',') {
        campos.push(actual)
        actual = ''
      } else actual += c
    }
    campos.push(actual)
    return campos
  })
}

const numero = (v: unknown): number => (v === null || v === undefined || v === '' ? NaN : Number(v))

/** `criminalidad.csv` (líneas `#` ignoradas); `cod_ine` siempre como texto. */
export function leerCriminalidad(texto: string): FilaCriminalidad[] {
  const [cabecera, ...cuerpo] = filasCsv(texto)
  if (!cabecera) return []
  const col = (nombre: string) => cabecera.indexOf(nombre)
  const [iCod, iMun, iTasa, iPer] = ['cod_ine', 'municipio', 'tasa_criminalidad', 'periodo'].map(col) as [number, number, number, number]
  return cuerpo.map((f) => ({
    cod_ine: String(f[iCod] ?? '').trim(),
    municipio: f[iMun] ?? '',
    tasa_criminalidad: numero(f[iTasa]),
    periodo: iPer === -1 ? 'Q1 2026' : (f[iPer] ?? ''),
  }))
}

/** Propiedades de cada feature de `secciones_renta.geojson` como filas. */
export function leerSecciones(geo: GeoJson): FilaSeccion[] {
  return geo.features.map(({ properties: p }) => {
    const renta = numero(p.renta_persona)
    return {
      cusec: String(p.cusec),
      cod_ine: String(p.cod_ine),
      municipio: String(p.municipio),
      renta_persona: Number.isNaN(renta) ? null : renta,
      anio: p.anio === undefined || p.anio === null ? '2023' : String(p.anio),
    }
  })
}

// ── Figuras ─────────────────────────────────────────────────────────────────

interface EspecCoropleta {
  geojson: GeoJson
  clave: string
  locations: string[]
  z: number[]
  escala: Escala
  factorMin: number
  hovertext: string[]
  hovertemplate: string
  customdata: unknown[][]
  titulo: string
  zoom: number
}

function coropleta(e: EspecCoropleta): Figura {
  const validos = e.z.filter((v) => !Number.isNaN(v))
  return {
    data: [
      {
        type: 'choroplethmap',
        geojson: e.geojson,
        featureidkey: e.clave,
        locations: e.locations,
        z: e.z,
        colorscale: e.escala,
        zmin: Math.min(...validos) * e.factorMin,
        zmax: Math.max(...validos) * 1.05,
        marker: { opacity: OPACIDAD },
        hovertext: e.hovertext,
        customdata: e.customdata,
        hovertemplate: e.hovertemplate,
        colorbar: colorbar(e.titulo),
      },
    ],
    layout: { ...LAYOUT_MAPA, map: { style: ESTILO, center: CENTRO, zoom: e.zoom } },
  }
}

/** Vista A (app.py:2455-2481). */
export function figuraCriminalidad(filas: FilaCriminalidad[], geojson: GeoJson): Figura {
  return coropleta({
    geojson,
    clave: 'properties.cod_ine',
    locations: filas.map((f) => String(f.cod_ine)),
    z: filas.map((f) => f.tasa_criminalidad),
    escala: COLOR_CRIMINALIDAD,
    factorMin: 0.85,
    hovertext: filas.map((f) => f.municipio),
    hovertemplate: '<b>%{hovertext}</b><br>Tasa / 100 000 hab=%{z:.0f}<br>Período=%{customdata[0]}<extra></extra>',
    customdata: filas.map((f) => [f.periodo]),
    titulo: 'Tasa / 100 000 hab',
    zoom: 9,
  })
}

/** Vista B (app.py:2520-2551): las secciones sin renta no se pintan. */
export function figuraRenta(filas: FilaSeccion[], geojson: GeoJson): Figura {
  const conRenta = filas.filter((f) => f.renta_persona !== null)
  return coropleta({
    geojson,
    clave: 'properties.cusec',
    locations: conRenta.map((f) => f.cusec),
    z: conRenta.map((f) => f.renta_persona as number),
    escala: COLOR_RENTA,
    factorMin: 0.9,
    hovertext: conRenta.map((f) => f.municipio),
    hovertemplate:
      '<b>%{hovertext}</b><br>Sección censal=%{location}<br>Renta neta media (€/pers)=%{z:,.0f}<br>Año=%{customdata[0]}<extra></extra>',
    customdata: conRenta.map((f) => [f.anio]),
    titulo: 'Renta neta media (€/pers)',
    zoom: 10,
  })
}

/** Vista C (app.py:2653-2681). */
export function figuraPrecio(filas: FilaPrecio[], geojson: GeoJson): Figura {
  return coropleta({
    geojson,
    clave: 'properties.cod_ine',
    locations: filas.map((f) => f.cod_ine),
    z: filas.map((f) => f.eur_m2_med),
    escala: COLOR_PRECIO,
    factorMin: 0.9,
    hovertext: filas.map((f) => f.nombre),
    hovertemplate:
      '<b>%{hovertext}</b><br>€/m² (mediana)=%{z:,.0f}<br>Precio mediano (€)=%{customdata[0]:,.0f}<br>Anuncios=%{customdata[1]}<extra></extra>',
    customdata: filas.map((f) => [f.precio_med, f.n_listings]),
    titulo: '€/m² mediana',
    zoom: 9,
  })
}

// ── Joins y agregados ───────────────────────────────────────────────────────

/** Municipios del geojson sin fila de criminalidad (grises), ordenados por nombre (app.py:2484-2489). */
export function sinDatoCriminalidad(filas: FilaCriminalidad[], geojson: GeoJson): string[] {
  const codigos = new Set(filas.map((f) => String(f.cod_ine)))
  return geojson.features
    .filter((f) => !codigos.has(String(f.properties.cod_ine)))
    .map((f) => String(f.properties.nombre))
    .sort()
}

/** `_slug_muni` (app.py:2613): minúsculas, sin diacríticos, espacios y guiones → `_`, sin `'`. */
export function slugMunicipio(nombre: string): string {
  return nombre
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{Mn}/gu, '')
    .replaceAll(' ', '_')
    .replaceAll('-', '_')
    .replaceAll("'", '')
}

function mediana(xs: number[]): number {
  const s = [...xs].sort((a, b) => a - b)
  const m = s.length >> 1
  return s.length % 2 ? s[m]! : (s[m - 1]! + s[m]!) / 2
}

/** Agregado por municipio de app.py:2628-2640 (mediana €/m², mediana precio, nº de anuncios). */
export function agregarPrecios(listings: Listing[], geojson: GeoJson): FilaPrecio[] {
  const slugACod: Record<string, string> = {}
  const codANombre: Record<string, string> = {}
  for (const f of geojson.features) {
    const cod = String(f.properties.cod_ine)
    const nombre = String(f.properties.nombre)
    slugACod[slugMunicipio(nombre)] = cod
    codANombre[cod] = nombre
  }
  const grupos = new Map<string, Listing[]>()
  for (const l of listings) {
    if (l.eur_m2 === null || !l.municipio) continue
    const g = grupos.get(l.municipio)
    if (g) g.push(l)
    else grupos.set(l.municipio, [l])
  }
  const filas: FilaPrecio[] = []
  for (const municipio of [...grupos.keys()].sort()) {
    const cod = slugACod[municipio]
    if (cod === undefined) continue
    const g = grupos.get(municipio)!
    filas.push({
      municipio,
      cod_ine: cod,
      nombre: codANombre[cod]!,
      eur_m2_med: mediana(g.map((l) => l.eur_m2 as number)),
      precio_med: mediana(g.map((l) => l.price)),
      n_listings: g.length,
    })
  }
  return filas
}

// ── Rankings (app.py:2504-2514, 2580-2594, 2696-2714) ───────────────────────

const decimales0 = (v: number) => (Number.isNaN(v) ? 'nan' : v.toFixed(0))
const miles = (v: number) => (Number.isNaN(v) ? 'nan' : v.toLocaleString('en-US', { maximumFractionDigits: 0 }))

/** Orden estable; los NaN van al final (pandas `sort_values`). */
function ordenar<T>(xs: T[], clave: (x: T) => number, descendente: boolean): T[] {
  return [...xs].sort((a, b) => {
    const ka = clave(a)
    const kb = clave(b)
    if (Number.isNaN(ka) || Number.isNaN(kb)) return Number.isNaN(ka) ? (Number.isNaN(kb) ? 0 : 1) : -1
    return descendente ? kb - ka : ka - kb
  })
}

export function rankingCriminalidad(filas: FilaCriminalidad[]): { Municipio: string; 'Tasa / 100 000 hab': string }[] {
  return ordenar(filas, (f) => f.tasa_criminalidad, true).map((f) => ({
    Municipio: f.municipio,
    'Tasa / 100 000 hab': decimales0(f.tasa_criminalidad),
  }))
}

export function rankingRenta(
  filas: FilaSeccion[],
): { Municipio: string; 'Sección censal': string; 'Renta neta media (€/pers)': string }[] {
  const conRenta = filas.filter((f) => f.renta_persona !== null)
  return ordenar(conRenta, (f) => f.renta_persona as number, true).map((f) => ({
    Municipio: f.municipio,
    'Sección censal': f.cusec,
    'Renta neta media (€/pers)': miles(f.renta_persona as number),
  }))
}

/** Ascendente: el más barato primero. */
export function rankingPrecio(
  filas: FilaPrecio[],
): { Municipio: string; '€/m² mediana': string; 'Precio mediano (€)': string; Anuncios: number }[] {
  return ordenar(filas, (f) => f.eur_m2_med, false).map((f) => ({
    Municipio: f.nombre,
    '€/m² mediana': miles(f.eur_m2_med),
    'Precio mediano (€)': miles(f.precio_med),
    Anuncios: f.n_listings,
  }))
}

// ── Notas (markdown mínimo: `**negrita**`) ──────────────────────────────────

export const notaCriminalidad = (periodo: string) =>
  `**Fuente**: Portal Estadístico de Criminalidad · Ministerio del Interior · **Período**: ${periodo} · **Métrica**: infracciones penales / 100 000 hab · **Rojo** = más peligroso · **Verde** = más seguro · **Gris** = sin publicación oficial (<20 000 hab)`

export const notaRenta = (anio: string, sinRenta: number) =>
  `**Fuente**: Atlas de Distribución de Renta de los Hogares (ADRH ${anio}) · INE · **Métrica**: renta neta media por persona (€/año) · **Verde** = renta alta · **Rojo** = renta baja · **Gris** = sin publicación oficial (${sinRenta} secciones) · ⚠️ Renta ≠ criminalidad — proxy socioeconómico del barrio`

export const notaPrecio = (sinPrecio: number) =>
  `**Fuente**: anuncios scrapeados (pisos.com + fotocasa) · **Métrica**: mediana de €/m² por municipio · **Verde** = más barato · **Rojo** = más caro · **Gris** = sin anuncios (${sinPrecio} municipios)`
