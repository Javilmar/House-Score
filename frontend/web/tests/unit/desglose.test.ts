import { describe, expect, it } from 'vitest'
import { breakdownScoreDetails, parseScoreDetails } from '../../src/domain/desglose'

describe('parseScoreDetails (app.py:642)', () => {
  it('clasifica en features, penalties y bonuses y pasa cada texto por clean', () => {
    const r = parseScoreDetails({
      score_details: [
        '🏊 Piscina (+15)',
        '🚗 Garaje (+5)',
        '⚠️ Sin ascensor (-10)',
        '🕸️ Anuncio antiguo (-5)',
        '❓ Sin m² (-3)',
        '💰 Precio bajo (+20)',
        '📐 Tamaño (+8)',
        '💎 Chollo (+10)',
        '📉 Bajada (+5)',
        'sin emoji',
      ],
    })
    expect(r.features).toEqual(['Piscina (+15)', 'Garaje (+5)'])
    expect(r.penalties).toEqual(['Sin ascensor (-10)', 'Anuncio antiguo (-5)', 'Sin m² (-3)'])
    expect(r.bonuses).toEqual(['Precio bajo (+20)', 'Tamaño (+8)', 'Chollo (+10)', 'Bajada (+5)'])
  })
  it('las penalizaciones tienen prioridad y luego las características', () => {
    const r = parseScoreDetails({ score_details: ['⚠️ 🏊 mixto', '🚇 Metro 💰'] })
    expect(r.penalties).toEqual(['mixto'])
    expect(r.features).toEqual(['Metro'])
    expect(r.bonuses).toEqual([])
  })
  it('todos los emojis de característica', () => {
    const emojis = ['🏊', '🚗', '📦', '🌿', '🏡', '🛗', '🌳', '🏗️', '🔧', '🚇', '🏢', '⚡', '📅']
    expect(parseScoreDetails({ score_details: emojis.map((e) => `${e} x`) }).features).toHaveLength(13)
  })
  it('ausente o vacío → listas vacías', () => {
    expect(parseScoreDetails({ score_details: [] })).toEqual({ features: [], penalties: [], bonuses: [] })
  })
})

describe('breakdownScoreDetails (app.py:688)', () => {
  it('extrae puntos del último paréntesis y reconcilia con el score', () => {
    const r = breakdownScoreDetails({
      score: 35,
      score_details: ['💰 Precio/m² bajo (+20)', '🏊 (+15)'],
    })
    expect(r.scoreFinal).toBe(35)
    expect(r.items).toEqual([
      { label: '💰 Precio/m² bajo', points: 20, categoria: 'mercado' },
      { label: '🏊 Piscina', points: 15, categoria: 'características' },
    ])
  })
  it('acepta "pts" y signo; sin paréntesis → 0 puntos', () => {
    const r = breakdownScoreDetails({
      score: 5,
      score_details: ['⚠️ Penaliza (-5 pts)', '📅 Sin dato', '🔧 Reformar (+10pts)'],
    })
    expect(r.items.map((i) => [i.label, i.points, i.categoria])).toEqual([
      ['⚠️ Penaliza', -5, 'penalización'],
      ['📅 Sin dato', 0, 'estado'],
      ['🔧 Reformar', 10, 'estado'],
    ])
  })
  it('línea de tope de características', () => {
    const r = breakdownScoreDetails({ score: 15, score_details: ['(características capadas: 25→15)'] })
    expect(r.items[0]).toEqual({ label: 'Características (tope: 25→15)', points: -10, categoria: 'características' })
    const r2 = breakdownScoreDetails({ score: 0, score_details: ['Características Capadas: 30>20'] })
    expect(r2.items[0]).toEqual({ label: 'Características (tope: 30→20)', points: -10, categoria: 'características' })
  })
  it('categorías por orden de prioridad', () => {
    const cat = (d: string) => breakdownScoreDetails({ score: 0, score_details: [d] }).items[0]!.categoria
    expect(cat('💎 x (+1)')).toBe('valor')
    expect(cat('❓ x (+1)')).toBe('valor')
    expect(cat('📐 x (+1)')).toBe('tamaño')
    expect(cat('🛗 x (+1)')).toBe('características')
    expect(cat('🏗️ x (+1)')).toBe('estado')
    expect(cat('🚇 x (+1)')).toBe('ubicación')
    expect(cat('⚡ x (+1)')).toBe('ubicación')
    expect(cat('📉 x (+1)')).toBe('mercado')
    expect(cat('🕸️ x (+1)')).toBe('penalización')
    expect(cat('otra cosa (+1)')).toBe('otro')
    // 💎 va antes que 📐 y que las características
    expect(cat('💎 📐 🏊 x (+1)')).toBe('valor')
  })
  it('expande los emojis de característica solos', () => {
    const emojis: [string, string][] = [
      ['🏊', 'Piscina'],
      ['🚗', 'Garaje'],
      ['📦', 'Trastero'],
      ['🌿', 'Terraza'],
      ['🏡', 'Patio'],
      ['🛗', 'Ascensor'],
      ['🌳', 'Jardín'],
    ]
    for (const [e, n] of emojis) {
      expect(breakdownScoreDetails({ score: 3, score_details: [`${e} (+3)`] }).items[0]!.label).toBe(`${e} ${n}`)
    }
    expect(breakdownScoreDetails({ score: 3, score_details: ['🏊 Cubierta (+3)'] }).items[0]!.label).toBe('🏊 Cubierta')
  })
  it('añade "Ajuste (límite 0-100)" cuando la suma no cuadra', () => {
    const neg = breakdownScoreDetails({ score: 100, score_details: ['💰 a (+80)', '💰 b (+40)'] })
    expect(neg.items.at(-1)).toEqual({ label: 'Ajuste (límite 0-100)', points: -20, categoria: 'penalización' })
    const pos = breakdownScoreDetails({ score: 10, score_details: ['⚠️ a (-5)'] })
    expect(pos.items.at(-1)).toEqual({ label: 'Ajuste (límite 0-100)', points: 15, categoria: 'otro' })
  })
  it('sin ajuste cuando cuadra', () => {
    const r = breakdownScoreDetails({ score: 7, score_details: ['💰 a (+10)', '⚠️ b (-3)'] })
    expect(r.items).toHaveLength(2)
  })
  it('score final: entero truncado; 0 si falta; elementos no texto se saltan', () => {
    expect(breakdownScoreDetails({ score: 63.9, score_details: [] }).scoreFinal).toBe(63)
    expect(breakdownScoreDetails({ score: 0, score_details: [] })).toEqual({ items: [], scoreFinal: 0 })
    const r = breakdownScoreDetails({ score: 0, score_details: [42 as unknown as string, null as unknown as string] })
    expect(r.items).toEqual([])
  })
  it('sin detalles y score > 0 → solo el ajuste', () => {
    const r = breakdownScoreDetails({ score: 40, score_details: [] })
    expect(r.items).toEqual([{ label: 'Ajuste (límite 0-100)', points: 40, categoria: 'otro' }])
  })
})
