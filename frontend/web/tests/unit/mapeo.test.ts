import { describe, expect, it } from 'vitest'
import { mapearHistorico, mapearListing, mapearListings } from '../../src/api/mapeo'
import type { ListingApi, PasadaDiariaApi } from '../../src/types'
import { historicoApi, listingsApi } from '../fixtures'

const listings = listingsApi()
const historico = historicoApi()

const base = (extra: Partial<ListingApi> = {}): ListingApi => ({
  url: 'https://x/1',
  titulo: 'Piso',
  precio: 200000,
  m2: 100,
  habitaciones: 3,
  banos: 2,
  municipio: 'getafe',
  fuente: 'pisos.com',
  score: 61.5,
  datos_insuficientes: false,
  estado: 'activo',
  primera_aparicion: '2026-07-01',
  ultima_aparicion: '2026-07-20',
  precio_anterior: 210000,
  bajada_precio: 10000,
  detalle: {},
  ...extra,
})

describe('mapearListing: campos principales (_PRINCIPALES)', () => {
  it('traduce cada campo de la API a la columna de app.py con una fila real', () => {
    const api = listings[0]!
    const l = mapearListing(api)
    expect(l.title).toBe(api.titulo)
    expect(l.price).toBe(api.precio ?? 0)
    expect(l.m2).toBe(api.m2 ?? 0)
    expect(l.rooms).toBe(api.habitaciones ?? 0)
    expect(l.bathrooms).toBe(api.banos ?? 0)
    expect(l.url).toBe(api.url)
    expect(l.source).toBe(api.fuente)
    expect(l.municipio).toBe(api.municipio)
    expect(l.score).toBe(api.score ?? 0)
    expect(l.datos_insuficientes).toBe(api.datos_insuficientes)
    expect(l.first_seen).toBe(api.primera_aparicion)
    expect(l.last_seen).toBe(api.ultima_aparicion)
    expect(l.price_drop).toBe(api.bajada_precio)
    expect(l.previous_price).toBe(api.precio_anterior)
  })

  it('traduce precio, m², habitaciones, baños y score sintéticos', () => {
    const l = mapearListing(base())
    expect(l).toMatchObject({
      title: 'Piso',
      price: 200000,
      m2: 100,
      rooms: 3,
      bathrooms: 2,
      url: 'https://x/1',
      source: 'pisos.com',
      municipio: 'getafe',
      score: 61.5,
      datos_insuficientes: false,
      first_seen: '2026-07-01',
      last_seen: '2026-07-20',
      price_drop: 10000,
      previous_price: 210000,
    })
  })

  it('estado: activo→active, retirado→delisted, desconocido se conserva', () => {
    expect(mapearListing(base({ estado: 'activo' })).status).toBe('active')
    expect(mapearListing(base({ estado: 'retirado' })).status).toBe('delisted')
    expect(mapearListing(base({ estado: 'pausado' })).status).toBe('pausado')
  })

  it('price, m2, rooms, bathrooms y score ausentes (null) valen 0', () => {
    const l = mapearListing(
      base({ precio: null, m2: null, habitaciones: null, banos: null, score: null }),
    )
    expect([l.price, l.m2, l.rooms, l.bathrooms, l.score]).toEqual([0, 0, 0, 0, 0])
  })

  it('price_drop y previous_price ausentes siguen siendo null (no se rellenan)', () => {
    const l = mapearListing(base({ bajada_precio: null, precio_anterior: null }))
    expect(l.price_drop).toBeNull()
    expect(l.previous_price).toBeNull()
  })

  it('fechas inválidas o ausentes → null (NaT)', () => {
    const l = mapearListing(
      base({ primera_aparicion: 'no-fecha', ultima_aparicion: null as unknown as string }),
    )
    expect(l.first_seen).toBeNull()
    expect(l.last_seen).toBeNull()
  })

  it('valores numéricos como texto se convierten; texto no numérico → 0 en las 5 columnas con cero', () => {
    const l = mapearListing(
      base({ precio: '150000' as unknown as number, m2: 'abc' as unknown as number }),
    )
    expect(l.price).toBe(150000)
    expect(l.m2).toBe(0)
  })
})

describe('mapearListing: detalle', () => {
  it('rellena con defectos neutros cuando el detalle viene vacío', () => {
    const l = mapearListing(base({ detalle: {} }))
    expect(l).toMatchObject({
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
    })
  })

  it('detalle null o ausente equivale a vacío', () => {
    const l = mapearListing(base({ detalle: null as unknown as ListingApi['detalle'] }))
    expect(l.cumple_requisitos).toBe(true)
    expect(l.features).toEqual([])
  })

  it('los valores null del detalle toman el defecto; los falsy válidos se conservan', () => {
    const l = mapearListing(
      base({
        detalle: {
          location: null,
          exterior: false,
          cumple_requisitos: false,
          year_built: null,
          floor: '',
          features: null,
        },
      }),
    )
    expect(l.location).toBe('')
    expect(l.cumple_requisitos).toBe(false)
    expect(l.year_built).toBe(0)
    expect(l.features).toEqual([])
  })

  it('los defectos mutables no se comparten entre listings', () => {
    const a = mapearListing(base())
    const b = mapearListing(base())
    a.features.push('x')
    a.detail_features['k'] = 1
    a.score_details.push('y')
    expect(b.features).toEqual([])
    expect(b.detail_features).toEqual({})
    expect(b.score_details).toEqual([])
  })

  it('pasa cada campo del detalle de una fila real', () => {
    const api = listings.find((x) => (x.detalle['score_details'] as unknown[]).length > 0)!
    const d = api.detalle
    const l = mapearListing(api)
    expect(l.location).toBe(d['location'])
    expect(l.description).toBe(d['description'])
    expect(l.floor).toBe(d['floor'])
    expect(l.conservation).toBe(d['conservation'])
    expect(l.energy_rating).toBe(d['energy_rating'])
    expect(l.pisos_id).toBe(d['pisos_id'])
    expect(l.features).toEqual(d['features'])
    expect(l.detail_features).toEqual(d['detail_features'])
    expect(l.score_details).toEqual(d['score_details'])
    expect(l.exterior).toBe(d['exterior'])
    expect(l.cumple_requisitos).toBe(d['cumple_requisitos'])
    expect(l.year_built).toBe(d['year_built'])
  })

  it('claves extra del detalle pasan como columnas (crashed_municipio de una fila real)', () => {
    const api = listings.find((x) => 'crashed_municipio' in x.detalle)!
    expect(mapearListing(api).crashed_municipio).toBe(api.detalle['crashed_municipio'])
    const l = mapearListing(base({ detalle: { campo_nuevo: 'v' } }))
    expect((l as unknown as Record<string, unknown>)['campo_nuevo']).toBe('v')
  })

  it('una clave del detalle nunca pisa una principal', () => {
    const l = mapearListing(
      base({ detalle: { title: 'del detalle', price: 1, score: 99, status: 'x', source: 'y' } }),
    )
    expect(l.title).toBe('Piso')
    expect(l.price).toBe(200000)
    expect(l.score).toBe(61.5)
    expect(l.status).toBe('active')
    expect(l.source).toBe('pisos.com')
  })

  it('year_built y valores numéricos del detalle como texto se convierten', () => {
    expect(mapearListing(base({ detalle: { year_built: '1999' } })).year_built).toBe(1999)
  })
})

describe('mapearListing: eur_m2', () => {
  it('descarta el eur_m2 del detalle y lo recalcula = round(precio / m²)', () => {
    const l = mapearListing(base({ precio: 250001, m2: 100, detalle: { eur_m2: 5 } }))
    expect(l.eur_m2).toBe(2500)
  })

  it('m² = 0 o ausente → null (no inf)', () => {
    expect(mapearListing(base({ m2: 0 })).eur_m2).toBeNull()
    expect(mapearListing(base({ m2: null })).eur_m2).toBeNull()
  })

  it('precio ausente con m² válido → 0 (precio fillna 0)', () => {
    expect(mapearListing(base({ precio: null })).eur_m2).toBe(0)
  })

  it('redondea half-to-even como pandas (round(0))', () => {
    expect(mapearListing(base({ precio: 250, m2: 100 })).eur_m2).toBe(2) // 2.5 → 2
    expect(mapearListing(base({ precio: 350, m2: 100 })).eur_m2).toBe(4) // 3.5 → 4
  })
})

describe('mapearListings', () => {
  it('ordena por score descendente (estable) y mapea todo el fixture real', () => {
    const out = mapearListings(listings)
    expect(out).toHaveLength(listings.length)
    for (let i = 1; i < out.length; i++) expect(out[i - 1]!.score).toBeGreaterThanOrEqual(out[i]!.score)
  })

  it('lista vacía → lista vacía', () => {
    expect(mapearListings([])).toEqual([])
  })
})

describe('mapearHistorico', () => {
  it('renombra columnas (_HISTORICO) y ordena por fecha ascendente', () => {
    const filas: PasadaDiariaApi[] = [
      { fecha: '2026-07-16', total_listings: 3, score_medio: 20.5, precio_medio: 200, precio_min: 100, precio_max: 300 },
      { fecha: '2026-07-14', total_listings: 1, score_medio: null, precio_medio: null, precio_min: null, precio_max: null },
    ]
    const out = mapearHistorico(filas)
    expect(out.map((r) => r.fecha)).toEqual(['2026-07-14', '2026-07-16'])
    expect(out[1]).toEqual({
      fecha: '2026-07-16',
      count: 3,
      avg_score: 20.5,
      avg_price: 200,
      min_price: 100,
      max_price: 300,
    })
    expect(out[0]).toMatchObject({ count: 1, avg_score: null, avg_price: null, min_price: null, max_price: null })
  })

  it('mapea el fixture real completo', () => {
    const out = mapearHistorico(historico)
    expect(out).toHaveLength(historico.length)
    for (let i = 1; i < out.length; i++) expect(out[i - 1]!.fecha! <= out[i]!.fecha!).toBe(true)
    const primera = historico.reduce((a, b) => (a.fecha < b.fecha ? a : b))
    expect(out[0]!.count).toBe(primera.total_listings)
  })

  it('fecha inválida → null y valores no numéricos → null', () => {
    const out = mapearHistorico([
      { fecha: 'zz', total_listings: 'x' as unknown as number, score_medio: 1, precio_medio: 1, precio_min: 1, precio_max: 1 },
    ])
    expect(out[0]!.fecha).toBeNull()
    expect(out[0]!.count).toBeNull()
  })

  it('vacío → vacío', () => {
    expect(mapearHistorico([])).toEqual([])
  })
})
