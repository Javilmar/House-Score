/**
 * Figuras de "Evolución y análisis" (app.py:1590-1695) como `{data, layout}` de Plotly,
 * con la plantilla `style_fig` (app.py:617-636).
 */
import type { Listing, PasadaDiaria } from '../types'
import { ACCENT, BORDER, GRID, INK, MUTED, SUBTLE, SURFACE } from '../styles/tema'

export interface Figura {
  data: Record<string, unknown>[]
  layout: Record<string, unknown>
}

export const MENSAJE_MINIMO_EVOLUCION = 'Se necesitan al menos 2 días de datos para ver evolución.'

/** `not diario.empty and len(diario) > 1` (app.py:1601). */
export const hayEvolucion = (diario: readonly PasadaDiaria[]): boolean => diario.length > 1

/** `style_fig(fig, title)`: fondo transparente, ejes y tipografías del tema. */
function styleFig(titulo?: string): Record<string, unknown> {
  return {
    title: titulo ? { text: titulo, font: { size: 16, color: INK, family: 'Fraunces' } } : undefined,
    font: { family: 'Inter', size: 12, color: MUTED },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 12, r: 12, t: titulo ? 44 : 12, b: 12 },
    height: 350,
    legend: { bgcolor: 'rgba(0,0,0,0)', font: { size: 11 } },
    hoverlabel: { bgcolor: SURFACE, bordercolor: BORDER, font: { family: 'Inter', color: INK } },
    xaxis: { showgrid: false, zeroline: false, linecolor: BORDER, tickcolor: BORDER },
    yaxis: { showgrid: true, gridcolor: GRID, zeroline: false, linecolor: 'rgba(0,0,0,0)' },
  }
}

/** Fusiona como `update_layout`: los diccionarios anidados se combinan, el resto se sustituye. */
function fusionar(base: Record<string, unknown>, extra: Record<string, unknown>): Record<string, unknown> {
  const salida = { ...base }
  for (const [k, v] of Object.entries(extra)) {
    const previo = salida[k]
    salida[k] =
      v && typeof v === 'object' && !Array.isArray(v) && previo && typeof previo === 'object'
        ? fusionar(previo as Record<string, unknown>, v as Record<string, unknown>)
        : v
  }
  return salida
}

const fechas = (d: readonly PasadaDiaria[]) => d.map((f) => f.fecha)

/** fig1: barras de listings + score medio en eje secundario (app.py:1602-1633). */
export function figuraEvolucionListings(diario: readonly PasadaDiaria[]): Figura {
  return {
    data: [
      {
        type: 'bar',
        x: fechas(diario),
        y: diario.map((f) => f.count),
        name: 'Listings',
        marker: { color: SUBTLE, line: { width: 0 } },
      },
      {
        type: 'scatter',
        x: fechas(diario),
        y: diario.map((f) => f.avg_score),
        name: 'Score medio',
        yaxis: 'y2',
        line: { color: ACCENT, width: 2.5 },
      },
    ],
    layout: fusionar(styleFig('Listings y score medio por día'), {
      yaxis: { title: undefined },
      yaxis2: { title: undefined, overlaying: 'y', side: 'right', range: [0, 100], showgrid: false },
      legend: { x: 0.01, y: 0.99 },
    }),
  }
}

/** fig2: precio medio, mínimo y máximo por día (app.py:1635-1664). */
export function figuraEvolucionPrecios(diario: readonly PasadaDiaria[]): Figura {
  const punteada = { color: SUBTLE, width: 1.5, dash: 'dot' }
  return {
    data: [
      {
        type: 'scatter',
        x: fechas(diario),
        y: diario.map((f) => f.avg_price),
        mode: 'lines+markers',
        name: 'Medio',
        line: { color: ACCENT, width: 2.5 },
      },
      { type: 'scatter', x: fechas(diario), y: diario.map((f) => f.min_price), mode: 'lines', name: 'Mínimo', line: punteada },
      { type: 'scatter', x: fechas(diario), y: diario.map((f) => f.max_price), mode: 'lines', name: 'Máximo', line: { ...punteada } },
    ],
    layout: styleFig('Evolución de precios (€)'),
  }
}

/** fig3: histograma de 20 bins del score sobre todos los listings (app.py:1671-1677). */
export function figuraHistogramaScores(listings: readonly Listing[]): Figura {
  return {
    data: [
      {
        type: 'histogram',
        x: listings.map((l) => l.score),
        nbinsx: 20,
        opacity: 0.85,
        marker: { color: ACCENT, line: { width: 0 } },
      },
    ],
    layout: fusionar(styleFig(), { xaxis: { title: { text: 'Score' } }, yaxis: { title: undefined }, bargap: 0.08 }),
  }
}

/** fig4: 10 ubicaciones más frecuentes (value_counts: orden estable, sin nulos) (app.py:1681-1695). */
export function figuraTopUbicaciones(listings: readonly Listing[]): Figura {
  const cuenta = new Map<string, number>()
  for (const l of listings) {
    if (l.location == null) continue
    cuenta.set(l.location, (cuenta.get(l.location) ?? 0) + 1)
  }
  const top = [...cuenta.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)
  return {
    data: [
      {
        type: 'bar',
        orientation: 'h',
        x: top.map(([, n]) => n),
        y: top.map(([u]) => u),
        marker: { color: ACCENT, line: { width: 0 } },
      },
    ],
    layout: fusionar(styleFig(), {
      xaxis: { title: undefined },
      yaxis: { title: undefined, autorange: 'reversed' },
    }),
  }
}
