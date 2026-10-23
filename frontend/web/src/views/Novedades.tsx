/** Pestaña «Novedades» (app.py `with tab5:`, 1807-1935). */
import { useMemo, useState } from 'react'
import ListingCard from '../components/ListingCard'
import Selector from '../components/Selector'
import {
  fechasNovedades,
  nuevosDe,
  ORDEN_NOVEDADES_DEFECTO,
  ORDENES_NOVEDADES,
  textosNovedad,
  type OrdenNovedades,
} from '../domain/tarjetas'
import { useDatos } from '../state/datos'

export default function Novedades() {
  const { activos } = useDatos()
  const fechas = useMemo(() => fechasNovedades(activos), [activos])
  const [pasada, setPasada] = useState<string | null>(null)
  const [orden, setOrden] = useState<OrdenNovedades>(ORDEN_NOVEDADES_DEFECTO)
  const fecha = pasada !== null && fechas.includes(pasada) ? pasada : fechas[0]
  const nuevos = useMemo(() => (fecha === undefined ? [] : nuevosDe(activos, fecha, orden)), [activos, fecha, orden])

  return (
    <>
      <h2 className="sr-only-vista">Novedades</h2>
      <h3>Pisos nuevos por pasada</h3>
      {fecha === undefined ? (
        <div className="aviso aviso-info" role="status">
          No hay datos de ejecuciones disponibles.
        </div>
      ) : (
        <>
          <div className="f-controles">
            <Selector etiqueta="Pasada" opciones={fechas} valor={fecha} onChange={setPasada} />
            <Selector etiqueta="Ordenar por" opciones={ORDENES_NOVEDADES} valor={orden} onChange={setOrden} />
          </div>
          <div className="lc-contador">
            {nuevos.length}
            <span>pisos nuevos en esta pasada</span>
          </div>
          {nuevos.length === 0 ? (
            <div className="aviso aviso-info" role="status">
              No hay pisos nuevos en esta pasada.
            </div>
          ) : (
            nuevos.map((l, i) => {
              const { meta, detalles, precio } = textosNovedad(l)
              return (
                <ListingCard
                  key={l.url || i}
                  variante="compacta"
                  listing={l}
                  lineas={[meta, detalles]}
                  precio={<div className="lc-precio">{precio}</div>}
                />
              )
            })
          )}
        </>
      )}
    </>
  )
}
