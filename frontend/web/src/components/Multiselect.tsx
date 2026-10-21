import { useId } from 'react'

interface Props {
  etiqueta: string
  opciones: string[]
  valor: string[]
  onChange: (valor: string[]) => void
}

/** Selector múltiple (st.multiselect): desplegable con casillas; sin selección = sin filtro. */
export default function Multiselect({ etiqueta, opciones, valor, onChange }: Props) {
  const id = useId()
  return (
    <div className="f-campo">
      <span className="f-etiqueta" id={id}>
        {etiqueta}
      </span>
      <details className="f-multi">
        <summary aria-labelledby={id}>{valor.length > 0 ? valor.join(', ') : 'Elegir opciones'}</summary>
        <div className="f-multi-lista" role="group" aria-labelledby={id}>
          {opciones.length === 0 && <span className="f-multi-vacio">Sin opciones</span>}
          {opciones.map((o) => (
            <label key={o}>
              <input
                type="checkbox"
                checked={valor.includes(o)}
                onChange={(e) => onChange(e.target.checked ? [...valor, o] : valor.filter((v) => v !== o))}
              />
              {o}
            </label>
          ))}
        </div>
      </details>
    </div>
  )
}
