/** Cálculo hipotecario: port literal de `calc_impuestos` (app.py:791) y `calc_hipoteca` (app.py:824). */

// Fiscalidad orientativa 2024-2026 (app.py:54-63)
export const IVA_OBRA_NUEVA = 0.1
export const ITP: Record<string, number> = { 'Comunidad de Madrid': 0.06, 'Castilla-La Mancha': 0.09 }
export const AJD: Record<string, number> = { 'Comunidad de Madrid': 0.0075, 'Castilla-La Mancha': 0.015 }
export const OTROS_GASTOS_PCT = 0.015
export const TASACION_EUR = 400
export const CCAA_DEFAULT = 'Comunidad de Madrid'
export const HIP_DEFAULTS = { entrada_pct: 0.2, plazo: 30, tin: 0.03 }

export interface Impuestos {
  items: [string, number][]
  total: number
}

export interface ResultadoHipoteca {
  principal: number
  entrada: number
  cuota_mensual: number
  impuestos: Impuestos
  otros_gastos: number
  ahorro_necesario: number
  total_intereses: number
  total_pagado: number
}

/** `round()` de Python 3: las mitades exactas van al entero par. */
export function pyRound(x: number): number {
  const f = Math.floor(x)
  const d = x - f
  if (d < 0.5) return f
  if (d > 0.5) return f + 1
  return f % 2 === 0 ? f : f + 1
}

const tipoDe = (tabla: Record<string, number>, ccaa: string): number =>
  (Object.prototype.hasOwnProperty.call(tabla, ccaa) ? tabla[ccaa] : undefined) ?? tabla[CCAA_DEFAULT] ?? 0

export function calcImpuestos(precio: number, esObraNueva: boolean, ccaa: string): Impuestos {
  const p = Number(precio)
  if (!(p > 0 && Number.isFinite(p))) return { items: [], total: 0 }

  if (esObraNueva) {
    const iva = pyRound(p * IVA_OBRA_NUEVA)
    const ajdTipo = tipoDe(AJD, ccaa)
    const ajd = pyRound(p * ajdTipo)
    return {
      items: [
        ['IVA (10%)', iva],
        [`AJD (${(ajdTipo * 100).toFixed(2)}% — ${ccaa})`, ajd],
      ],
      total: iva + ajd,
    }
  }
  const itpTipo = tipoDe(ITP, ccaa)
  const itp = pyRound(p * itpTipo)
  return { items: [[`ITP (${(itpTipo * 100).toFixed(0)}% — ${ccaa})`, itp]], total: itp }
}

export function calcHipoteca(
  precio: number,
  entradaPct: number,
  plazoAnios: number,
  tin: number,
  esObraNueva: boolean,
  ccaa: string,
): ResultadoHipoteca {
  const p = Number(precio)
  if (!(p > 0 && Number.isFinite(p))) {
    return {
      principal: 0,
      entrada: 0,
      cuota_mensual: 0,
      impuestos: { items: [], total: 0 },
      otros_gastos: 0,
      ahorro_necesario: 0,
      total_intereses: 0,
      total_pagado: 0,
    }
  }

  const entrada = pyRound(p * entradaPct)
  const principal = pyRound(p - entrada)
  const n = Math.trunc(plazoAnios) * 12
  const r = tin / 12

  let cuota: number
  if (r > 0 && n > 0) cuota = (principal * r) / (1 - (1 + r) ** -n)
  else if (n > 0) cuota = principal / n
  else cuota = 0

  const totalPagadoPrestamo = cuota * n
  const totalIntereses = Math.max(0, totalPagadoPrestamo - principal)

  const impuestos = calcImpuestos(p, esObraNueva, ccaa)
  const otrosGastos = pyRound(p * OTROS_GASTOS_PCT) + TASACION_EUR
  const ahorroNecesario = entrada + impuestos.total + otrosGastos

  return {
    principal,
    entrada,
    cuota_mensual: pyRound(cuota),
    impuestos,
    otros_gastos: otrosGastos,
    ahorro_necesario: ahorroNecesario,
    total_intereses: pyRound(totalIntereses),
    total_pagado: pyRound(totalPagadoPrestamo + entrada + impuestos.total + otrosGastos),
  }
}

/** `_hip_eur` (app.py:2021): miles con punto y sufijo « €». */
export const eur = (v: number): string =>
  String(pyRound(v)).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' €'

export interface Esfuerzo {
  gastos: number
  total: number
  ratio: number
  color: string
  bg: string
  border: string
}

/** Gastos mensuales y ratio de esfuerzo (app.py:2107-2122). `gastos` = suma de los sliders. */
export function esfuerzo(cuota: number, gastos: number, ingresos: number): Esfuerzo {
  const total = cuota + gastos
  const ratio = ingresos > 0 ? (total / ingresos) * 100 : 0
  const nivel = ratio < 30 ? 0 : ratio < 40 ? 1 : 2
  return {
    gastos,
    total,
    ratio,
    color: ['#4ade80', '#fb923c', '#f87171'][nivel] ?? '',
    bg: ['rgba(74,222,128,0.1)', 'rgba(251,146,60,0.1)', 'rgba(248,113,113,0.1)'][nivel] ?? '',
    border: ['rgba(74,222,128,0.25)', 'rgba(251,146,60,0.25)', 'rgba(248,113,113,0.25)'][nivel] ?? '',
  }
}
