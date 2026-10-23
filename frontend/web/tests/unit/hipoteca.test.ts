/** Valores esperados calculados ejecutando calc_impuestos/calc_hipoteca de app.py (Python). */
import { describe, expect, it } from 'vitest'
import {
  calcHipoteca,
  calcImpuestos,
  eur,
  esfuerzo,
  pyRound,
  CCAA_DEFAULT,
} from '../../src/domain/hipoteca'

const MAD = 'Comunidad de Madrid'
const CLM = 'Castilla-La Mancha'

describe('pyRound (round() de Python: mitades al par)', () => {
  it('redondea mitades al entero par', () => {
    expect(pyRound(62.5)).toBe(62)
    expect(pyRound(63.5)).toBe(64)
    expect(pyRound(18.75)).toBe(19)
    expect(pyRound(0.5)).toBe(0)
    expect(pyRound(2.4)).toBe(2)
  })
})

describe('calcImpuestos', () => {
  it('segunda mano Madrid: ITP 4 %', () => {
    expect(calcImpuestos(250000, false, MAD)).toEqual({
      items: [['ITP (4% — Comunidad de Madrid)', 10000]],
      total: 10000,
    })
  })
  it('segunda mano CLM: ITP 9 %', () => {
    expect(calcImpuestos(200000, false, CLM).total).toBe(18000)
  })
  it('obra nueva CLM: IVA 10 % + AJD 1,50 %', () => {
    expect(calcImpuestos(250000, true, CLM)).toEqual({
      items: [
        ['IVA (10%)', 25000],
        ['AJD (1.50% — Castilla-La Mancha)', 3750],
      ],
      total: 28750,
    })
  })
  it('obra nueva Madrid: AJD 0,75 % con redondeo bancario', () => {
    expect(calcImpuestos(2500, true, MAD)).toEqual({
      items: [
        ['IVA (10%)', 250],
        ['AJD (0.75% — Comunidad de Madrid)', 19],
      ],
      total: 269,
    })
    expect(calcImpuestos(1250, false, MAD).total).toBe(50)
  })
  it('CCAA desconocida usa el tipo de Madrid con la etiqueta dada', () => {
    expect(calcImpuestos(100000, false, 'Narnia').items).toEqual([['ITP (4% — Narnia)', 4000]])
  })
  it('precio no válido → vacío', () => {
    const vacio = { items: [], total: 0 }
    expect(calcImpuestos(0, false, MAD)).toEqual(vacio)
    expect(calcImpuestos(-5, false, MAD)).toEqual(vacio)
    expect(calcImpuestos(NaN, false, MAD)).toEqual(vacio)
    expect(calcImpuestos(Infinity, true, MAD)).toEqual(vacio)
  })
})

describe('calcHipoteca', () => {
  it('segunda mano Madrid, 20 %, 30 años, 3 %', () => {
    expect(calcHipoteca(250000, 0.2, 30, 0.03, false, MAD)).toEqual({
      principal: 200000,
      entrada: 50000,
      cuota_mensual: 843,
      impuestos: { items: [['ITP (4% — Comunidad de Madrid)', 10000]], total: 10000 },
      otros_gastos: 4150,
      ahorro_necesario: 64150,
      total_intereses: 103555,
      total_pagado: 367705,
    })
  })
  it('obra nueva CLM', () => {
    const h = calcHipoteca(250000, 0.2, 30, 0.03, true, CLM)
    expect(h.impuestos.total).toBe(28750)
    expect(h.ahorro_necesario).toBe(82900)
    expect(h.total_pagado).toBe(386455)
    expect(h.cuota_mensual).toBe(843)
  })
  it('extremos de sliders: 5 % entrada, 40 años, 8 %', () => {
    const h = calcHipoteca(200000, 0.05, 40, 0.08, false, CLM)
    expect(h).toMatchObject({
      principal: 190000,
      entrada: 10000,
      cuota_mensual: 1321,
      otros_gastos: 3400,
      ahorro_necesario: 31400,
      total_intereses: 444124,
      total_pagado: 665524,
    })
  })
  it('50 %, 5 años, 0,5 %, obra nueva Madrid, precio impar', () => {
    expect(calcHipoteca(123457, 0.5, 5, 0.005, true, MAD)).toMatchObject({
      principal: 61729,
      entrada: 61728,
      cuota_mensual: 1042,
      otros_gastos: 2252,
      ahorro_necesario: 77252,
      total_intereses: 788,
      total_pagado: 139769,
    })
  })
  it('100 % de entrada: sin préstamo', () => {
    expect(calcHipoteca(100000, 1, 30, 0.03, false, MAD)).toMatchObject({
      principal: 0,
      cuota_mensual: 0,
      total_intereses: 0,
      ahorro_necesario: 105900,
      total_pagado: 105900,
    })
  })
  it('interés 0 %: cuota = principal / n (sistema sin interés)', () => {
    expect(calcHipoteca(100000, 0.2, 30, 0, false, MAD)).toMatchObject({
      cuota_mensual: 222,
      total_intereses: 0,
      ahorro_necesario: 25900,
      total_pagado: 105900,
    })
  })
  it('precio 0 o inválido → todo a cero', () => {
    const cero = {
      principal: 0,
      entrada: 0,
      cuota_mensual: 0,
      impuestos: { items: [], total: 0 },
      otros_gastos: 0,
      ahorro_necesario: 0,
      total_intereses: 0,
      total_pagado: 0,
    }
    expect(calcHipoteca(0, 0.2, 30, 0.03, false, MAD)).toEqual(cero)
    expect(calcHipoteca(NaN, 0.2, 30, 0.03, false, MAD)).toEqual(cero)
  })
  it('precios mínimos con redondeo bancario', () => {
    expect(calcHipoteca(125, 0.5, 30, 0.03, false, MAD)).toMatchObject({
      principal: 63,
      entrada: 62,
      cuota_mensual: 0,
      otros_gastos: 402,
      ahorro_necesario: 469,
      total_intereses: 33,
      total_pagado: 565,
    })
    expect(calcHipoteca(10050, 0.2, 30, 0.03, false, MAD)).toMatchObject({
      entrada: 2010,
      cuota_mensual: 34,
      ahorro_necesario: 2963,
      total_pagado: 15166,
    })
  })
  it('CCAA por defecto', () => {
    expect(CCAA_DEFAULT).toBe(MAD)
  })
})

describe('eur', () => {
  it('miles con punto y símbolo €', () => {
    expect(eur(843)).toBe('843 €')
    expect(eur(1234567)).toBe('1.234.567 €')
    expect(eur(0)).toBe('0 €')
  })
})

describe('esfuerzo (gastos mensuales)', () => {
  it('ratio y total', () => {
    expect(esfuerzo(900, 80 + 50 + 30 + 80 + 35, 2500)).toMatchObject({
      gastos: 275,
      total: 1175,
      ratio: 47,
      color: '#f87171',
    })
    expect(esfuerzo(500, 275, 4000)).toMatchObject({ ratio: 19.375, color: '#4ade80', bg: 'rgba(74,222,128,0.1)', border: 'rgba(74,222,128,0.25)' })
  })
  it('umbrales: <30 verde, 30 naranja, <40 naranja, 40 rojo', () => {
    expect(esfuerzo(1199, 0, 4000).color).toBe('#4ade80')
    expect(esfuerzo(1200, 0, 4000)).toMatchObject({ color: '#fb923c', bg: 'rgba(251,146,60,0.1)', border: 'rgba(251,146,60,0.25)' })
    expect(esfuerzo(1599, 0, 4000).color).toBe('#fb923c')
    expect(esfuerzo(1600, 0, 4000)).toMatchObject({ color: '#f87171', bg: 'rgba(248,113,113,0.1)', border: 'rgba(248,113,113,0.25)' })
  })
  it('ingresos 0 → ratio 0', () => {
    expect(esfuerzo(500, 100, 0).ratio).toBe(0)
  })
})
