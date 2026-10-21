import type { Listing } from '../src/types'

/** Listing mínimo válido con los defectos de api_datos; `parcial` sobrescribe. */
export function listing(parcial: Partial<Listing> = {}): Listing {
  return {
    title: 'Piso en venta',
    price: 200000,
    m2: 80,
    rooms: 3,
    bathrooms: 1,
    url: 'https://www.pisos.com/x/1/',
    source: 'pisos.com',
    municipio: 'getafe',
    score: 50,
    datos_insuficientes: false,
    first_seen: '2026-07-01',
    last_seen: '2026-07-21',
    price_drop: null,
    previous_price: null,
    status: 'active',
    location: '',
    description: '',
    floor: '',
    conservation: '',
    energy_rating: '',
    pisos_id: '',
    features: [],
    detail_features: {},
    score_details: [],
    exterior: false,
    cumple_requisitos: true,
    year_built: 0,
    eur_m2: 2500,
    ...parcial,
  }
}
