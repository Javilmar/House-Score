import { describe, expect, it } from 'vitest'
import { calcularKpis } from '../../src/domain/kpis'
import { listing } from '../helpers'

const HOY = '2026-07-21'

const datos = [
  listing({ price: 100000, score: 80, status: 'active', first_seen: HOY }),
  listing({ price: 200000, score: 60, status: 'active', first_seen: '2026-07-01', price_drop: 5000 }),
  listing({ price: 300001, score: 40, status: 'delisted', first_seen: HOY, price_drop: 1000 }),
  listing({ price: 0, score: 0, status: 'active', datos_insuficientes: true, price_drop: 0 }),
]

describe('calcularKpis (app.py:987-1035)', () => {
  it('devuelve los 6 KPI en orden, con icono y etiqueta', () => {
    const k = calcularKpis(datos, HOY)
    expect(k.map((x) => [x.icono, x.etiqueta])).toEqual([
      ['layers', 'Total listings'],
      ['sparkles', 'Nuevos hoy'],
      ['star', 'Score medio'],
      ['wallet', 'Precio medio'],
      ['trending-down', 'Bajadas'],
      ['ruler', 'Sin valorar'],
    ])
  })

  it('Total listings = solo activos', () => {
    expect(calcularKpis(datos, HOY)[0]!.valor).toBe('3')
  })
  it('Nuevos hoy = first_seen == hoy entre los activos (excluye retirados)', () => {
    expect(calcularKpis(datos, HOY)[1]!.valor).toBe('1')
    expect(calcularKpis(datos, '2030-01-01')[1]!.valor).toBe('0')
  })
  it('Score medio = media de los fiables activos con 1 decimal', () => {
    // fiables activos: 80, 60 → 70.0
    expect(calcularKpis(datos, HOY)[2]!.valor).toBe('70.0')
  })
  it('Score medio usa todo df si no hay fiables', () => {
    const todos = [listing({ score: 10, datos_insuficientes: true }), listing({ score: 21, datos_insuficientes: true })]
    expect(calcularKpis(todos, HOY)[2]!.valor).toBe('15.5')
  })
  it('Precio medio sobre activos (incluye price=0, excluye retirados), coma de miles', () => {
    // (100000+200000+0)/3 = 100000
    expect(calcularKpis(datos, HOY)[3]!.valor).toBe('100,000 €')
    expect(calcularKpis([listing({ price: 1234567 })], HOY)[3]!.valor).toBe('1,234,567 €')
    expect(calcularKpis([listing({ price: 999 })], HOY)[3]!.valor).toBe('999 €')
  })
  it('Bajadas = price_drop > 0 solo en activos', () => {
    expect(calcularKpis(datos, HOY)[4]!.valor).toBe('1')
  })
  it('Sin valorar = datos_insuficientes', () => {
    expect(calcularKpis(datos, HOY)[5]!.valor).toBe('1')
  })
  it('lista vacía: cifras a cero y "—" donde no hay media', () => {
    const k = calcularKpis([], HOY)
    expect(k.map((x) => x.valor)).toEqual(['0', '0', '—', '—', '0', '0'])
  })
  it('solo retirados: se comporta como lista vacía', () => {
    const k = calcularKpis([listing({ status: 'delisted', price: 1, score: 9 })], HOY)
    expect(k.map((x) => x.valor)).toEqual(['0', '0', '—', '—', '0', '0'])
  })
})
