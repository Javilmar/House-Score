/**
 * Plantilla que `st.plotly_chart(theme="streamlit")` aplica por debajo de cada figura de app.py
 * (medida en el Streamlit original): lo que la figura fija explícitamente prevalece.
 */
type Dic = Record<string, unknown>

const COLORWAY = ['#83c9ff', '#0068c9', '#ffabab', '#ff2b2b', '#7defa1', '#29b09d', '#ffd16a', '#ff8700', '#6d3fc0', '#d5dae5']
const TEXTO_EJES = '#e6eaf1'
const TEXTO_LEYENDA = '#fafafa'

const esDic = (v: unknown): v is Dic => typeof v === 'object' && v !== null && !Array.isArray(v)

/** `base` por debajo, `extra` por encima; los diccionarios se combinan en profundidad. */
function combina(base: Dic, extra: Dic): Dic {
  const salida: Dic = { ...base }
  for (const [k, v] of Object.entries(extra)) {
    if (v === undefined) continue
    const previo = salida[k]
    salida[k] = esDic(v) && esDic(previo) ? combina(previo, v) : v
  }
  return salida
}

const esEje = (k: string) => /^[xy]axis\d*$/.test(k)

/** Eje x al fondo con 20 px de separación del título, eje y con 24 px (valores de la plantilla de Streamlit). */
const plantillaEje = (k: string, eje: unknown): Dic => ({
  automargin: true,
  tickfont: { color: TEXTO_EJES },
  title: { standoff: k.startsWith('x') ? 20 : 24, font: { color: TEXTO_EJES } },
  // plotly.js reciente sincroniza las marcas de un eje superpuesto con las del principal; Streamlit las deja automáticas
  ...(esDic(eje) && eje.overlaying !== undefined ? { tickmode: 'auto' } : {}),
})

export function conTemaStreamlit(layout: Dic | undefined): Dic {
  const l = layout ?? {}
  const base: Dic = {
    colorway: COLORWAY,
    margin: { pad: 8 },
    legend: { font: { color: TEXTO_LEYENDA } },
    hoverlabel: { font: { size: 12 } },
  }
  for (const k of Object.keys(l)) if (esEje(k)) base[k] = plantillaEje(k, l[k])
  const salida = combina(base, l)
  const titulo = salida.title
  if (esDic(titulo) && typeof titulo.text === 'string' && titulo.text !== '') {
    const negrita = titulo.text.startsWith('<b>') ? titulo.text : `<b>${titulo.text}</b>`
    salida.title = combina({ x: 0, xanchor: 'left', pad: { l: 4 } }, { ...titulo, text: negrita })
  }
  return salida
}

/** Barra de color: la plantilla de Streamlit la separa 24 px del borde y le añade un contorno transparente de 8 px. */
export function conTemaStreamlitDatos(data: readonly unknown[]): unknown[] {
  return data.map((traza) =>
    esDic(traza) && esDic(traza.colorbar)
      ? { ...traza, colorbar: { xpad: 24, outlinewidth: 8, outlinecolor: 'transparent', ...traza.colorbar } }
      : traza,
  )
}
