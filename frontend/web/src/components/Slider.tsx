import { useId, type CSSProperties } from 'react'

interface Props {
  etiqueta: string
  min: number
  max: number
  step?: number
  value: number
  onChange: (valor: number) => void
  formato?: (n: number) => string
  className?: string
}

/** Fracción 0–1 de `v` dentro de [min, max]. */
export function fraccion(v: number, min: number, max: number): number {
  return max > min ? Math.min(1, Math.max(0, (v - min) / (max - min))) : 0
}

/** Slider simple (st.slider): pista fina con tramo relleno, valor actual sobre el tirador y extremos al pasar el ratón. */
export default function Slider({ etiqueta, min, max, step = 1, value, onChange, formato = String, className }: Props) {
  const id = useId()
  const estilo = { '--p': fraccion(value, min, max) } as CSSProperties
  return (
    <div className={`f-campo st-slider-campo${className ? ` ${className}` : ''}`}>
      <label className="f-etiqueta" htmlFor={id}>
        {etiqueta}
      </label>
      <div className="st-slider" style={estilo}>
        <span className="st-slider-valor">{formato(value)}</span>
        <input
          id={id}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          disabled={min >= max}
          onChange={(e) => onChange(Number(e.target.value))}
        />
        <div className="st-slider-extremos" aria-hidden="true">
          <span>{formato(min)}</span>
          <span>{formato(max)}</span>
        </div>
      </div>
    </div>
  )
}
