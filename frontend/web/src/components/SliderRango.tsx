import { useId } from 'react'
import type { Rango } from '../domain/filtros'

interface Props {
  etiqueta: string
  min: number
  max: number
  step?: number
  valor: Rango
  onChange: (valor: Rango) => void
  formato?: (n: number) => string
}

/** Slider de rango (st.slider con tupla): dos controles, mínimo y máximo, y los valores actuales. */
export default function SliderRango({ etiqueta, min, max, step = 1, valor, onChange, formato = String }: Props) {
  const id = useId()
  // El máximo del DOM es el primer paso ≥ max, para poder llegar a `max` aunque no caiga en la rejilla
  const topeDom = min + Math.ceil((max - min) / step) * step
  const acota = (n: number) => Math.min(max, Math.max(min, n))
  return (
    <div className="f-campo">
      <span className="f-etiqueta" id={id}>
        {etiqueta}
      </span>
      <span className="f-valores">
        {formato(valor[0])} – {formato(valor[1])}
      </span>
      <input
        type="range"
        aria-label={`${etiqueta} (mínimo)`}
        min={min}
        max={topeDom}
        step={step}
        value={valor[0]}
        disabled={min >= max}
        onChange={(e) => onChange([Math.min(acota(Number(e.target.value)), valor[1]), valor[1]])}
      />
      <input
        type="range"
        aria-label={`${etiqueta} (máximo)`}
        min={min}
        max={topeDom}
        step={step}
        value={valor[1]}
        disabled={min >= max}
        onChange={(e) => onChange([valor[0], Math.max(acota(Number(e.target.value)), valor[0])])}
      />
    </div>
  )
}
