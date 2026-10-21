import { describe, expect, it } from 'vitest'
import { mapearHistorico, mapearListings } from '../../src/api/mapeo'
import {
  MENSAJE_MINIMO_EVOLUCION,
  hayEvolucion,
  figuraEvolucionListings,
  figuraEvolucionPrecios,
  figuraHistogramaScores,
  figuraTopUbicaciones,
} from '../../src/domain/graficos'
import { ACCENT, BORDER, GRID, INK, MUTED, SUBTLE, SURFACE } from '../../src/styles/tema'
import type { Listing } from '../../src/types'
import { historicoApi, listingsApi } from '../fixtures'

const historico = mapearHistorico(historicoApi())
const listings = mapearListings(listingsApi())
type Obj = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any

describe('hayEvolucion (mínimo de 2 días)', () => {
  it('exige más de una fila y publica el mensaje literal', () => {
    expect(hayEvolucion([])).toBe(false)
    expect(hayEvolucion(historico.slice(0, 1))).toBe(false)
    expect(hayEvolucion(historico.slice(0, 2))).toBe(true)
    expect(hayEvolucion(historico)).toBe(true)
    expect(MENSAJE_MINIMO_EVOLUCION).toBe('Se necesitan al menos 2 días de datos para ver evolución.')
  })
})

describe('figuraEvolucionListings (fig1)', () => {
  const { data, layout } = figuraEvolucionListings(historico) as unknown as { data: [Obj, Obj]; layout: Obj }
  it('barras de listings + línea de score medio en eje y2', () => {
    expect(data).toHaveLength(2)
    expect(data[0]).toMatchObject({
      type: 'bar',
      name: 'Listings',
      marker: { color: SUBTLE, line: { width: 0 } },
    })
    expect(data[0].x).toEqual(historico.map((h) => h.fecha))
    expect(data[0].y).toEqual(historico.map((h) => h.count))
    expect(data[1]).toMatchObject({
      type: 'scatter',
      name: 'Score medio',
      yaxis: 'y2',
      line: { color: ACCENT, width: 2.5 },
    })
    expect(data[1].y).toEqual(historico.map((h) => h.avg_score))
  })
  it('layout: título, eje dual 0-100 y leyenda arriba a la izquierda', () => {
    expect(layout.title).toMatchObject({ text: 'Listings y score medio por día', font: { size: 16, color: INK } })
    expect(layout.yaxis2).toMatchObject({ overlaying: 'y', side: 'right', range: [0, 100], showgrid: false })
    expect(layout.yaxis.title).toBeUndefined()
    expect(layout.legend).toMatchObject({ x: 0.01, y: 0.99 })
    expect(layout.height).toBe(350)
    expect(layout.margin).toEqual({ l: 12, r: 12, t: 44, b: 12 })
  })
})

describe('figuraEvolucionPrecios (fig2)', () => {
  const { data, layout } = figuraEvolucionPrecios(historico) as unknown as { data: [Obj, Obj, Obj]; layout: Obj }
  it('tres series medio/mínimo/máximo', () => {
    expect(data.map((d) => d.name)).toEqual(['Medio', 'Mínimo', 'Máximo'])
    expect(data.map((d) => d.mode)).toEqual(['lines+markers', 'lines', 'lines'])
    expect(data[0].line).toEqual({ color: ACCENT, width: 2.5 })
    expect(data[1].line).toEqual({ color: SUBTLE, width: 1.5, dash: 'dot' })
    expect(data[2].line).toEqual({ color: SUBTLE, width: 1.5, dash: 'dot' })
    expect(data[0].y).toEqual(historico.map((h) => h.avg_price))
    expect(data[1].y).toEqual(historico.map((h) => h.min_price))
    expect(data[2].y).toEqual(historico.map((h) => h.max_price))
    expect(data[2].x).toEqual(historico.map((h) => h.fecha))
  })
  it('layout de style_fig con título', () => {
    expect(layout.title.text).toBe('Evolución de precios (€)')
    expect(layout.yaxis2).toBeUndefined()
  })
})

describe('figuraHistogramaScores (fig3)', () => {
  const { data, layout } = figuraHistogramaScores(listings) as unknown as { data: [Obj]; layout: Obj }
  it('histograma de 20 bins sobre todos los listings (incluye retirados)', () => {
    expect(data).toHaveLength(1)
    expect(data[0]).toMatchObject({
      type: 'histogram',
      nbinsx: 20,
      opacity: 0.85,
      marker: { color: ACCENT, line: { width: 0 } },
    })
    expect(data[0].x).toEqual(listings.map((l) => l.score))
    expect(listings.some((l) => l.status !== 'active')).toBe(true)
  })
  it('layout sin título, eje x "Score" y bargap 0.08', () => {
    expect(layout.title).toBeUndefined()
    expect(layout.margin).toEqual({ l: 12, r: 12, t: 12, b: 12 })
    expect(layout.xaxis.title).toMatchObject({ text: 'Score' })
    expect(layout.yaxis.title).toBeUndefined()
    expect(layout.bargap).toBe(0.08)
  })
})

describe('figuraTopUbicaciones (fig4)', () => {
  const { data, layout } = figuraTopUbicaciones(listings) as unknown as { data: [Obj]; layout: Obj }
  it('barras horizontales con las 10 ubicaciones más frecuentes', () => {
    const cuenta = new Map<string, number>()
    for (const l of listings) cuenta.set(l.location, (cuenta.get(l.location) ?? 0) + 1)
    const esperado = [...cuenta.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)
    expect(data[0]).toMatchObject({ type: 'bar', orientation: 'h', marker: { color: ACCENT, line: { width: 0 } } })
    expect(data[0].x).toEqual(esperado.map(([, n]) => n))
    expect(data[0].y).toEqual(esperado.map(([u]) => u))
    expect(data[0].y.length).toBeLessThanOrEqual(10)
    expect(data[0].y.length).toBeGreaterThan(0)
  })
  it('layout: y invertido para que la mayor quede arriba', () => {
    expect(layout.yaxis.autorange).toBe('reversed')
    expect(layout.xaxis.title).toBeUndefined()
    expect(layout.yaxis.title).toBeUndefined()
  })
  it('empate: conserva el orden de primera aparición (value_counts estable)', () => {
    const base = listings[0]
    const mk = (location: string): Listing => ({ ...base!, location })
    const f = figuraTopUbicaciones([mk('B'), mk('A'), mk('A'), mk('C'), mk('B')]) as unknown as { data: [Obj] }
    expect(f.data[0].y).toEqual(['B', 'A', 'C'])
    expect(f.data[0].x).toEqual([2, 2, 1])
  })
})

describe('style_fig', () => {
  it('tipografías, fondos transparentes y ejes', () => {
    const { layout } = figuraEvolucionPrecios(historico) as { layout: Obj }
    expect(layout.font).toMatchObject({ family: 'Inter', size: 12, color: MUTED })
    expect(layout.paper_bgcolor).toBe('rgba(0,0,0,0)')
    expect(layout.plot_bgcolor).toBe('rgba(0,0,0,0)')
    expect(layout.hoverlabel).toMatchObject({ bgcolor: SURFACE, bordercolor: BORDER, font: { family: 'Inter', color: INK } })
    expect(layout.xaxis).toMatchObject({ showgrid: false, zeroline: false, linecolor: BORDER, tickcolor: BORDER })
    expect(layout.yaxis).toMatchObject({ showgrid: true, gridcolor: GRID, zeroline: false, linecolor: 'rgba(0,0,0,0)' })
  })
})
