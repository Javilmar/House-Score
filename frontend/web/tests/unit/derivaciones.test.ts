import { describe, expect, it } from 'vitest'
import {
  clean,
  colorDias,
  diasEnMercado,
  esRetirado,
  fmtEur,
  municipioDe,
  redondear,
  scoreColor,
  sinAcentos,
  tipoVivienda,
  zona,
  zonaACcaa,
} from '../../src/domain/derivaciones'
import { listing } from '../helpers'

describe('clean (app.py:340)', () => {
  it('quita emojis y recorta espacios y "·" de los extremos', () => {
    expect(clean('🏊 Piscina (+15)')).toBe('Piscina (+15)')
    expect(clean('⚠️ Sin ascensor')).toBe('Sin ascensor')
    expect(clean(' · Hola · ')).toBe('Hola')
    expect(clean('a · b')).toBe('a · b')
  })
  it('quita los selectores de variación y ZWJ', () => {
    expect(clean('🏗️ Obra')).toBe('Obra')
    expect(clean('x\u200dy\ufe0f')).toBe('xy')
  })
  it('texto sin emojis queda igual', () => {
    expect(clean('Piso en Getafe')).toBe('Piso en Getafe')
  })
})

describe('sinAcentos / zona (app.py:383-395)', () => {
  it('NFKD sin marcas y en minúsculas', () => {
    expect(sinAcentos('Seseña LEGANÉS')).toBe('sesena leganes')
  })
  it('Madrid Sur, Toledo Norte y "—"', () => {
    expect(zona('Piso en Getafe')).toBe('Madrid Sur')
    expect(zona('Chalet', 'en Seseña')).toBe('Toledo Norte')
    expect(zona('Móstoles')).toBe('Madrid Sur')
    expect(zona('Torrejón de la Calzada')).toBe('Madrid Sur')
    expect(zona('Toledo centro')).toBe('—')
    expect(zona()).toBe('—')
  })
  it('Madrid Sur tiene prioridad sobre Toledo Norte', () => {
    expect(zona('entre Illescas y Getafe')).toBe('Madrid Sur')
  })
  it('búsqueda por subcadena ("pinto" casa con "pintor")', () => {
    expect(zona('calle del pintor Sorolla')).toBe('Madrid Sur')
  })
  it('ignora textos vacíos o nulos', () => {
    expect(zona('', null, undefined, 'Ugena')).toBe('Toledo Norte')
  })
  it('zonaACcaa', () => {
    expect(zonaACcaa('Madrid Sur')).toBe('Comunidad de Madrid')
    expect(zonaACcaa('Toledo Norte')).toBe('Castilla-La Mancha')
    expect(zonaACcaa('—')).toBe('Comunidad de Madrid')
  })
})

describe('tipoVivienda (app.py:421)', () => {
  it('Obra nueva con cualquiera de las palabras clave', () => {
    for (const t of ['Obra nueva en Getafe', 'a ESTRENAR', 'Primera ocupación', 'Recién construido', 'llave en mano'])
      expect(tipoVivienda(t)).toBe('Obra nueva')
  })
  it('Segunda mano por defecto', () => {
    expect(tipoVivienda('Piso reformado', '', null)).toBe('Segunda mano')
    expect(tipoVivienda()).toBe('Segunda mano')
  })
  it('mira todos los textos', () => {
    expect(tipoVivienda('Piso', 'promoción nueva de pisos')).toBe('Obra nueva')
  })
})

describe('scoreColor (app.py:607) con los casos límite', () => {
  it.each([
    [100, '#22c55e'],
    [70, '#22c55e'],
    [69.99, '#84cc16'],
    [50, '#84cc16'],
    [49.99, '#eab308'],
    [35, '#eab308'],
    [34.9, '#f97316'],
    [20, '#f97316'],
    [19.99, '#ef4444'],
    [0, '#ef4444'],
    [-5, '#ef4444'],
    [Number.NaN, '#ef4444'],
  ])('%s → %s', (score, color) => {
    expect(scoreColor(score)).toBe(color)
  })
})

describe('días en mercado (app.py:1372-1385)', () => {
  it('diferencia en días entre hoy y first_seen', () => {
    expect(diasEnMercado('2026-07-01', '2026-07-21')).toBe(20)
    expect(diasEnMercado('2026-07-21', '2026-07-21')).toBe(0)
    expect(diasEnMercado('2026-02-28', '2026-03-01')).toBe(1)
    expect(diasEnMercado('2026-07-25', '2026-07-21')).toBe(-4)
  })
  it('sin fecha → null', () => {
    expect(diasEnMercado(null, '2026-07-21')).toBeNull()
  })
  it('colores: >45 rojo, >20 ámbar, resto gris', () => {
    expect(colorDias(46)).toBe('#f87171')
    expect(colorDias(45)).toBe('#fbbf24')
    expect(colorDias(21)).toBe('#fbbf24')
    expect(colorDias(20)).toBe('#a1a1aa')
    expect(colorDias(0)).toBe('#a1a1aa')
    expect(colorDias(null)).toBe('#a1a1aa')
  })
})

describe('retirado y municipio', () => {
  it('retirado ⇔ status delisted', () => {
    expect(esRetirado(listing({ status: 'delisted' }))).toBe(true)
    expect(esRetirado(listing({ status: 'active' }))).toBe(false)
  })
  it('municipio: campo con "_"→" " y capitalizado (str.title)', () => {
    expect(municipioDe(listing({ municipio: 'torrejon_de_la_calzada' }))).toBe('Torrejon De La Calzada')
    expect(municipioDe(listing({ municipio: 'getafe' }))).toBe('Getafe')
    expect(municipioDe(listing({ municipio: "o'brien" }))).toBe("O'Brien")
  })
  it('sin municipio: el texto entre paréntesis de location, o "—"', () => {
    expect(municipioDe(listing({ municipio: '', location: 'Calle X (Illescas)' }))).toBe('Illescas')
    expect(municipioDe(listing({ municipio: '  ', location: 'Zona ( Parla ) centro' }))).toBe('Parla')
    expect(municipioDe(listing({ municipio: '', location: 'sin paréntesis' }))).toBe('—')
  })
})

describe('formato de importes (_fmt_eur, app.py:1314)', () => {
  it('miles con punto y símbolo', () => {
    expect(fmtEur(249500)).toBe('249.500 €')
    expect(fmtEur(0)).toBe('0 €')
    expect(fmtEur(999)).toBe('999 €')
    expect(fmtEur(1234567)).toBe('1.234.567 €')
  })
  it('nulo o no finito → "—"', () => {
    expect(fmtEur(null)).toBe('—')
    expect(fmtEur(Number.NaN)).toBe('—')
    expect(fmtEur(Infinity)).toBe('—')
  })
  it('redondeo half-to-even de Python', () => {
    expect(fmtEur(2.5)).toBe('2 €')
    expect(fmtEur(3.5)).toBe('4 €')
    expect(redondear(0.5)).toBe(0)
    expect(redondear(1.5)).toBe(2)
    expect(redondear(-1.5)).toBe(-2)
    expect(redondear(2.4)).toBe(2)
  })
})
