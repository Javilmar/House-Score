import { describe, expect, it } from 'vitest'
import {
  descripcionTarjeta,
  fechasNovedades,
  fmtComa,
  fmtPunto,
  metaBajada,
  metaTop,
  nuevosDe,
  ordenarBajadas,
  paramsHipoteca,
  paramsHipotecaTarjeta,
  preciosBajada,
  textosNovedad,
  topNDeParam,
} from '../../src/domain/tarjetas'
import { listing } from '../helpers'

describe('formatos', () => {
  it('fmtComa = {:,.0f} de Python (coma, half-even)', () => {
    expect(fmtComa(1234567.5)).toBe('1,234,568')
    expect(fmtComa(0.5)).toBe('0')
    expect(fmtComa(2.5)).toBe('2')
    expect(fmtComa(NaN)).toBe('0')
  })
  it('fmtPunto = int() con punto de miles', () => {
    expect(fmtPunto(1234567.9)).toBe('1.234.567')
    expect(fmtPunto(950)).toBe('950')
  })
})

describe('parámetros', () => {
  it('topNDeParam acota a 5–30 y por defecto 15', () => {
    expect(topNDeParam(undefined)).toBe(15)
    expect(topNDeParam('abc')).toBe(15)
    expect(topNDeParam('2')).toBe(5)
    expect(topNDeParam('99')).toBe(30)
    expect(topNDeParam('22')).toBe(22)
  })
  it('paramsHipoteca trunca el precio y mapea tipo y CCAA', () => {
    expect(paramsHipoteca(199999.9, 'Obra nueva', 'Toledo Norte')).toEqual({ precio: 199999, tipo: 'obra-nueva', ccaa: 'clm' })
    expect(paramsHipoteca(0, 'Segunda mano', '—')).toEqual({ precio: 0, tipo: 'segunda-mano', ccaa: 'madrid' })
  })
  it('paramsHipotecaTarjeta deduce el tipo solo de título y descripción', () => {
    const l = listing({ price: 120000, title: 'Piso', description: 'Promoción de obra nueva', location: 'Illescas', features: ['obra nueva'] })
    expect(paramsHipotecaTarjeta(l)).toEqual({ precio: 120000, tipo: 'obra-nueva', ccaa: 'clm' })
    const sinPista = listing({ title: 'Piso', description: '', location: 'Getafe', features: ['obra nueva'] })
    expect(paramsHipotecaTarjeta(sinPista).tipo).toBe('segunda-mano')
  })
})

describe('Top: textos', () => {
  it('descripción: solo si supera 20 caracteres, truncada a 1500 y limpia', () => {
    expect(descripcionTarjeta('corta')).toBe('')
    expect(descripcionTarjeta('x'.repeat(20))).toBe('')
    expect(descripcionTarjeta('🏠 ' + 'a'.repeat(30))).toBe('a'.repeat(30))
    expect(descripcionTarjeta('b'.repeat(2000))).toHaveLength(1500)
  })
  it('meta: ubicación, planta, año, energía con "—" por defecto', () => {
    const l = listing({ location: '', floor: '', year_built: 1999, energy_rating: '' })
    expect(metaTop(l)).toEqual([
      ['map-pin', '—'],
      ['building', 'Planta'],
      ['calendar', '1999'],
      ['zap', '—'],
    ])
  })
})

describe('Bajadas', () => {
  const a = listing({ url: 'a', price: 180000, price_drop: 20000, previous_price: 200000, score: 40, first_seen: '2026-07-01' })
  const b = listing({ url: 'b', price: 90000, price_drop: 30000, previous_price: 120000, score: 60, first_seen: '2026-07-10' })
  const c = listing({ url: 'c', price: 100000, price_drop: 5000, previous_price: null, score: 50, first_seen: null })
  const d = listing({ url: 'd', price_drop: 0 })
  const e = listing({ url: 'e', price_drop: null })
  const todos = [a, b, c, d, e]
  const urls = (xs: { url: string }[]) => xs.map((x) => x.url)

  it('solo con price_drop > 0', () => {
    expect(urls(ordenarBajadas(todos, 'Mayor bajada (€)'))).toEqual(['b', 'a', 'c'])
  })
  it('Mayor bajada (%) = drop / (precio + drop)', () => {
    // a: 20/200 = 10 %, b: 30/120 = 25 %, c: 5/105 ≈ 4,8 %
    expect(urls(ordenarBajadas(todos, 'Mayor bajada (%)'))).toEqual(['b', 'a', 'c'])
    const x = listing({ url: 'x', price: 50000, price_drop: 50000 }) // 50 %
    expect(urls(ordenarBajadas([a, x], 'Mayor bajada (%)'))).toEqual(['x', 'a'])
  })
  it('Mejor score, Precio más bajo y Más reciente (sin fecha al final)', () => {
    expect(urls(ordenarBajadas(todos, 'Mejor score'))).toEqual(['b', 'c', 'a'])
    expect(urls(ordenarBajadas(todos, 'Precio más bajo'))).toEqual(['b', 'c', 'a'])
    expect(urls(ordenarBajadas(todos, 'Más reciente'))).toEqual(['b', 'a', 'c'])
  })
  it('precios: previo reconstruido si falta y % de bajada', () => {
    expect(preciosBajada(a)).toEqual({ actual: 180000, previo: 200000, pct: 10 })
    expect(preciosBajada(c)).toEqual({ actual: 100000, previo: 105000, pct: (5000 / 105000) * 100 })
    expect(preciosBajada(listing({ price: 0, price_drop: 0, previous_price: 0 })).pct).toBe(0)
  })
  it('meta con ubicación, fuente y días en mercado', () => {
    const l = listing({ location: '🏠 Getafe', source: 'pisos.com', first_seen: '2026-07-01' })
    expect(metaBajada(l, '2026-07-21')).toBe('Getafe · pisos.com · 20d en mercado')
    expect(metaBajada(listing({ location: '', source: '', first_seen: null }), '2026-07-21')).toBe('— · —')
  })
})

describe('Novedades', () => {
  const l1 = listing({ url: '1', first_seen: '2026-07-10', score: 50, price: 200000, m2: 80 })
  const l2 = listing({ url: '2', first_seen: '2026-07-10', score: 70, price: 300000, m2: 60 })
  const l3 = listing({ url: '3', first_seen: '2026-07-20', score: 10, price: 100000, m2: 100 })
  const l4 = listing({ url: '4', first_seen: null })
  const todos = [l1, l2, l3, l4]

  it('fechas distintas con aparición, la más reciente primero', () => {
    expect(fechasNovedades(todos)).toEqual(['2026-07-20', '2026-07-10'])
    expect(fechasNovedades([l4])).toEqual([])
  })
  it('nuevos de una pasada con las cuatro ordenaciones', () => {
    const u = (o: Parameters<typeof nuevosDe>[2]) => nuevosDe(todos, '2026-07-10', o).map((x) => x.url)
    expect(u('Mejor score')).toEqual(['2', '1'])
    expect(u('Precio más bajo')).toEqual(['1', '2'])
    expect(u('Mayor superficie')).toEqual(['1', '2'])
    expect(u('Más antiguo')).toEqual(['1', '2'])
  })
  it('textos: meta, detalles y precio con punto de miles', () => {
    const t = textosNovedad(listing({ location: 'Getafe', source: 'idealista', m2: 80.9, eur_m2: 3125.7, rooms: 3, price: 250000 }))
    expect(t).toEqual({ meta: 'Getafe · idealista', detalles: '80 m² · 3.125 €/m² · 3 hab', precio: '250.000 €' })
    const vacio = textosNovedad(listing({ location: '', source: '', eur_m2: null, price: Number.NaN, m2: Number.NaN, rooms: Number.NaN }))
    expect(vacio).toEqual({ meta: '—', detalles: '', precio: '—' })
  })
})
