import { useEffect, useRef, useState } from 'react'

interface Props {
  data: unknown[]
  layout?: Record<string, unknown>
  config?: Record<string, unknown>
  className?: string
}

type PlotlyModulo = typeof import('plotly.js-dist-min').default

/** Carga Plotly bajo demanda (trozo aparte) y dibuja `{data, layout, config}`. */
export default function Grafico({ data, layout, config, className }: Props) {
  const raiz = useRef<HTMLDivElement>(null)
  const [plotly, setPlotly] = useState<PlotlyModulo | null>(null)

  useEffect(() => {
    let vivo = true
    void import('plotly.js-dist-min').then((m) => {
      if (vivo) setPlotly(m.default ?? (m as unknown as PlotlyModulo))
    })
    return () => {
      vivo = false
    }
  }, [])

  useEffect(() => {
    const el = raiz.current
    if (!plotly || !el) return
    void plotly.react(el, data, { autosize: true, ...layout }, { responsive: true, displayModeBar: false, ...config })
  }, [plotly, data, layout, config])

  useEffect(() => {
    const el = raiz.current
    return () => {
      if (plotly && el) plotly.purge(el)
    }
  }, [plotly])

  return (
    <div className={className} style={{ width: '100%' }}>
      {plotly ? null : <p className="caption">Cargando gráfico…</p>}
      <div ref={raiz} style={{ width: '100%' }} />
    </div>
  )
}
