/** Paleta y escalas de app.py:34-52 (valores literales; el CSS usa los mismos). */
export const ACCENT = '#6366f1'
export const INK = '#e4e4e7'
export const MUTED = '#a1a1aa'
export const SUBTLE = '#52525b'
export const BORDER = '#27272a'
export const SURFACE = '#18181b'
export const GRID = '#1f1f23'

/** Orden descendente de umbral: `score >= umbral` → color (app.py:43-49). */
export const SCORE_SCALE: readonly (readonly [number, string])[] = [
  [70, '#22c55e'],
  [50, '#84cc16'],
  [35, '#eab308'],
  [20, '#f97316'],
  [0, '#ef4444'],
]

export const SERIES = ['#6366f1', '#94a3b8', '#22d3ee', '#a78bfa', '#2dd4bf', '#94a3b8'] as const

export const FONT_DISPLAY = "'Fraunces', 'Times New Roman', serif"
export const FONT_SANS = "'Inter', system-ui, -apple-system, sans-serif"
export const FONT_MONO = "'JetBrains Mono', ui-monospace, monospace"
