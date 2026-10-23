import Grafico from '../components/Grafico'
import {
  MENSAJE_MINIMO_EVOLUCION,
  figuraEvolucionListings,
  figuraEvolucionPrecios,
  figuraHistogramaScores,
  figuraTopUbicaciones,
  hayEvolucion,
} from '../domain/graficos'
import { useDatos } from '../state/datos'
import '../styles/evolucion.css'

export default function Evolucion() {
  const { activos, historico } = useDatos()
  const conEvolucion = hayEvolucion(historico)
  const f1 = conEvolucion ? figuraEvolucionListings(historico) : null
  const f2 = conEvolucion ? figuraEvolucionPrecios(historico) : null
  const f3 = figuraHistogramaScores(activos)
  const f4 = figuraTopUbicaciones(activos)

  return (
    <div className="evolucion-cols">
      <h2 className="sr-only-vista">Evolución y análisis</h2>
      <section>
        <h3>Evolución diaria</h3>
        {f1 && f2 ? (
          <>
            <div data-testid="grafico-evolucion-listings">
              <Grafico data={f1.data} layout={f1.layout} />
            </div>
            <div data-testid="grafico-evolucion-precios">
              <Grafico data={f2.data} layout={f2.layout} />
            </div>
          </>
        ) : (
          <div className="aviso aviso-info">{MENSAJE_MINIMO_EVOLUCION}</div>
        )}
      </section>
      <section>
        <h3>Distribución de scores</h3>
        <div data-testid="grafico-distribucion-scores">
          <Grafico data={f3.data} layout={f3.layout} />
        </div>
        <h3>Top ubicaciones</h3>
        <div data-testid="grafico-top-ubicaciones">
          <Grafico data={f4.data} layout={f4.layout} />
        </div>
      </section>
    </div>
  )
}
