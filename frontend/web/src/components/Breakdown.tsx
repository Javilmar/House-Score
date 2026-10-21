import { useMemo, useState } from 'react'
import { breakdownScoreDetails } from '../domain/desglose'
import type { Listing } from '../types'

interface Props {
  listing: Pick<Listing, 'score' | 'score_details'>
  /** Monta las filas solo al abrir el desplegable (tablas con cientos de filas). */
  diferido?: boolean
}

/** `_render_breakdown_html` (app.py:762): `<details>` con el desglose; sin ítems no renderiza nada. */
export default function Breakdown({ listing, diferido = false }: Props) {
  const { items, scoreFinal } = useMemo(() => breakdownScoreDetails(listing), [listing])
  const [abierto, setAbierto] = useState(false)
  if (items.length === 0) return null
  const mostrar = !diferido || abierto
  return (
    <details className="score-breakdown" onToggle={diferido ? (e) => setAbierto(e.currentTarget.open) : undefined}>
      <summary>Ver desglose de puntuación</summary>
      <table className="sb-table">
        <tbody>
          {mostrar &&
            items.map((it, i) => (
              <tr className="sb-row" key={i}>
                <td>{it.label}</td>
                <td>
                  {it.points > 0 ? (
                    <span className="sb-pts-pos">+{it.points}</span>
                  ) : it.points < 0 ? (
                    <span className="sb-pts-neg">{it.points}</span>
                  ) : (
                    <span className="sb-pts-zero">0</span>
                  )}
                </td>
              </tr>
            ))}
          <tr className="sb-total">
            <td>Total</td>
            <td>{scoreFinal}</td>
          </tr>
        </tbody>
      </table>
    </details>
  )
}
