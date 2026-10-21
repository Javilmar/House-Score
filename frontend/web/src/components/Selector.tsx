import { useId } from 'react'
import '../styles/listing-card.css'

interface Props<T extends string> {
  etiqueta: string
  opciones: readonly T[]
  valor: T
  onChange: (valor: T) => void
}

/** Lista desplegable de una opción (st.selectbox). */
export default function Selector<T extends string>({ etiqueta, opciones, valor, onChange }: Props<T>) {
  const id = useId()
  return (
    <div className="f-campo f-select">
      <label className="f-etiqueta" htmlFor={id}>
        {etiqueta}
      </label>
      <select id={id} value={valor} onChange={(e) => onChange(e.target.value as T)}>
        {opciones.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  )
}
