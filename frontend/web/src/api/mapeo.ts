/**
 * Traducción API → modelo del front. Reproduce campo a campo `frontend/dashboard/api_datos.py`
 * (`listings_a_dataframe`, `historico_a_dataframe`); ver inventario-dashboard.md §datos.
 */
import type { DetalleApi, Listing, ListingApi, PasadaDiaria, PasadaDiariaApi } from '../types'

/** Campo de la API → columna (api_datos._PRINCIPALES). */
const PRINCIPALES = {
  titulo: 'title',
  precio: 'price',
  m2: 'm2',
  habitaciones: 'rooms',
  banos: 'bathrooms',
  url: 'url',
  fuente: 'source',
  municipio: 'municipio',
  score: 'score',
  datos_insuficientes: 'datos_insuficientes',
  primera_aparicion: 'first_seen',
  ultima_aparicion: 'last_seen',
  bajada_precio: 'price_drop',
  precio_anterior: 'previous_price',
} as const

const ESTADOS: Record<string, string> = { activo: 'active', retirado: 'delisted' }

/** api_datos._DEFECTOS_DETALLE: se aplica si el valor es null/ausente. */
const DEFECTOS_DETALLE: Record<string, () => unknown> = {
  location: () => '',
  description: () => '',
  floor: () => '',
  conservation: () => '',
  energy_rating: () => '',
  pisos_id: () => '',
  features: () => [],
  detail_features: () => ({}),
  score_details: () => [],
  exterior: () => false,
  cumple_requisitos: () => true,
  year_built: () => 0,
}

/** api_datos._CERO_SI_FALTA */
const CERO_SI_FALTA = ['price', 'm2', 'rooms', 'bathrooms', 'score'] as const
/** api_datos._NUMERICAS (pd.to_numeric(errors="coerce")) */
const NUMERICAS = [
  'price',
  'm2',
  'rooms',
  'bathrooms',
  'score',
  'year_built',
  'price_drop',
  'previous_price',
] as const

/** api_datos._HISTORICO */
const HISTORICO = {
  total_listings: 'count',
  score_medio: 'avg_score',
  precio_medio: 'avg_price',
  precio_min: 'min_price',
  precio_max: 'max_price',
} as const

/** Equivalente a pd.to_numeric(errors="coerce"): número finito o null. */
function aNumero(v: unknown): number | null {
  if (typeof v === 'number') return Number.isFinite(v) ? v : null
  if (typeof v === 'string' && v.trim() !== '') {
    const n = Number(v)
    return Number.isFinite(n) ? n : null
  }
  return null
}

/** Equivalente a pd.to_datetime(errors="coerce") → ISO yyyy-mm-dd o null (NaT). */
function aFecha(v: unknown): string | null {
  if (typeof v !== 'string') return null
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(v)
  if (!m) return null
  const t = new Date(`${m[1]}-${m[2]}-${m[3]}T00:00:00Z`)
  if (Number.isNaN(t.getTime()) || t.toISOString().slice(0, 10) !== `${m[1]}-${m[2]}-${m[3]}`) return null
  return `${m[1]}-${m[2]}-${m[3]}`
}

/** Redondeo half-to-even de Python/pandas (`round(0)`). */
function redondearPar(x: number): number {
  const f = Math.floor(x)
  const d = x - f
  if (d < 0.5) return f
  if (d > 0.5) return f + 1
  return f % 2 === 0 ? f : f + 1
}

export function mapearListing(api: ListingApi): Listing {
  const fila: Record<string, unknown> = { ...((api.detalle as DetalleApi | null) ?? {}) }
  delete fila['eur_m2'] // se recalcula abajo, como hacía cargar_datos()
  for (const [clave, defecto] of Object.entries(DEFECTOS_DETALLE)) {
    if (fila[clave] == null) fila[clave] = defecto()
  }
  const item = api as unknown as Record<string, unknown>
  for (const [origen, destino] of Object.entries(PRINCIPALES)) {
    fila[destino] = item[origen] ?? null // una clave del detalle nunca pisa una principal
  }
  fila['status'] = typeof item['estado'] === 'string' ? (ESTADOS[item['estado']] ?? item['estado']) : item['estado']

  for (const col of NUMERICAS) if (col in fila) fila[col] = aNumero(fila[col])
  for (const col of CERO_SI_FALTA) fila[col] = fila[col] ?? 0
  // year_built ilegible: 0 (NaN en pandas; ambos son "sin año" para los consumidores)
  fila['year_built'] ??= 0
  fila['first_seen'] = aFecha(fila['first_seen'])
  fila['last_seen'] = aFecha(fila['last_seen'])
  // m² = 0 no es un dato fiable: null (app.py protege con pd.notna)
  const m2 = fila['m2'] as number
  fila['eur_m2'] = m2 > 0 ? redondearPar((fila['price'] as number) / m2) : null
  return fila as unknown as Listing
}

/** `listings_a_dataframe`: mapea y ordena por score descendente. */
export function mapearListings(items: ListingApi[]): Listing[] {
  return items.map(mapearListing).sort((a, b) => b.score - a.score)
}

export function mapearHistorico(filas: PasadaDiariaApi[]): PasadaDiaria[] {
  const out = filas.map((f) => {
    const r = f as unknown as Record<string, unknown>
    const fila: Record<string, unknown> = { fecha: aFecha(r['fecha']) }
    for (const [origen, destino] of Object.entries(HISTORICO)) fila[destino] = aNumero(r[origen])
    return fila as unknown as PasadaDiaria
  })
  return out.sort((a, b) => (a.fecha ?? '\uffff').localeCompare(b.fecha ?? '\uffff'))
}
