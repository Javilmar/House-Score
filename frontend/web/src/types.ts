/** Detalle libre de la API (`ListingOut.detalle`); sus claves pasan tal cual al `Listing`. */
export type DetalleApi = Record<string, unknown>

/** Respuesta de `GET /listings` (backend/app/schemas.py:ListingOut). */
export interface ListingApi {
  url: string
  titulo: string
  precio: number | null
  m2: number | null
  habitaciones: number | null
  banos: number | null
  municipio: string
  fuente: string
  score: number | null
  datos_insuficientes: boolean
  estado: string
  primera_aparicion: string
  ultima_aparicion: string
  precio_anterior: number | null
  bajada_precio: number | null
  detalle: DetalleApi
}

/** Respuesta de `GET /historico` (backend/app/schemas.py:PasadaDiariaOut). */
export interface PasadaDiariaApi {
  fecha: string
  total_listings: number
  score_medio: number | null
  precio_medio: number | null
  precio_min: number | null
  precio_max: number | null
}

/**
 * Modelo del front: columnas de `app.py` tal como las producía `api_datos.py`.
 * Fechas como ISO `yyyy-mm-dd` (null = NaT de pandas).
 * `price`, `m2`, `rooms`, `bathrooms` y `score` valen 0 cuando faltan (`_CERO_SI_FALTA`);
 * `eur_m2` es null cuando m² no es > 0.
 */
export interface Listing {
  // principales (api_datos._PRINCIPALES)
  title: string
  price: number
  m2: number
  rooms: number
  bathrooms: number
  url: string
  source: string
  municipio: string
  score: number
  datos_insuficientes: boolean
  first_seen: string | null
  last_seen: string | null
  price_drop: number | null
  previous_price: number | null
  /** 'active' | 'delisted' (otro valor se conserva tal cual) */
  status: string
  // detalle con defecto (api_datos._DEFECTOS_DETALLE)
  location: string
  description: string
  floor: string
  conservation: string
  energy_rating: string
  pisos_id: string
  features: string[]
  detail_features: Record<string, unknown>
  score_details: string[]
  exterior: boolean
  cumple_requisitos: boolean
  year_built: number
  // derivado: precio / m² (redondeado), null si m² no es > 0
  eur_m2: number | null
  // claves extra del detalle que la API puede enviar
  crashed_municipio?: unknown
}

/** Fila de `GET /historico` con las columnas de `app.py` (api_datos._HISTORICO). */
export interface PasadaDiaria {
  fecha: string | null
  count: number | null
  avg_score: number | null
  avg_price: number | null
  min_price: number | null
  max_price: number | null
}
