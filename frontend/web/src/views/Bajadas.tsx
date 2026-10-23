/** Pestaña «Bajadas de precio» (app.py `with tab4:`, 1699-1803). */
import { useMemo } from 'react'
import ListingCard from '../components/ListingCard'
import Selector from '../components/Selector'
import { redondear } from '../domain/derivaciones'
import {
  fmtComa,
  hayBajada,
  metaBajada,
  ORDEN_BAJADAS_DEFECTO,
  ORDENES_BAJADAS,
  ordenarBajadas,
  ordenBajadasDeParam,
  preciosBajada,
} from '../domain/tarjetas'
import { useDatos } from '../state/datos'
import { useRuta } from '../state/router'

export default function Bajadas() {
  const { activos, hoy } = useDatos()
  const { params, setParams } = useRuta()
  const orden = ordenBajadasDeParam(params.orden)
  const hay = useMemo(() => activos.some(hayBajada), [activos])
  const filas = useMemo(() => ordenarBajadas(activos, orden), [activos, orden])

  return (
    <>
      <h2 className="sr-only-vista">Bajadas de precio</h2>
      <h3>Listings con bajada de precio detectada</h3>
      {hay ? (
        <>
          <div className="f-top">
            <Selector
              etiqueta="Ordenar por"
              opciones={ORDENES_BAJADAS}
              valor={orden}
              onChange={(o) => setParams({ orden: o === ORDEN_BAJADAS_DEFECTO ? undefined : o })}
            />
          </div>
          {filas.map((l, i) => {
            const { actual, previo, pct } = preciosBajada(l)
            return (
              <ListingCard
                key={l.url || i}
                variante="compacta"
                listing={l}
                lineas={[metaBajada(l, hoy)]}
                precio={
                  <>
                    <div className="lc-precio-previo" style={{ textDecoration: 'line-through' }}>{fmtComa(previo)} €</div>
                    <div className="lc-precio">{fmtComa(actual)} €</div>
                  </>
                }
                extra={<div className="score-badge lc-badge-bajada">−{redondear(pct)}%</div>}
              />
            )
          })}
        </>
      ) : (
        <div className="aviso aviso-info" role="status">
          No se han detectado bajadas de precio todavía. Aparecerán aquí cuando un listing baje entre pasadas.
        </div>
      )}
    </>
  )
}
