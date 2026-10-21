import type { EstadoCarga as Estado } from '../state/carga'
import type { TipoError } from '../api/cliente'
import '../styles/estado.css'

export type EstadoNoListo = Exclude<Estado, { fase: 'listo' }>

interface Props {
  estado: EstadoNoListo
  reintentar: () => void
}

const TITULO: Record<TipoError, string> = {
  no_disponible: 'API no disponible',
  limite: 'Demasiadas peticiones',
  http: 'Error del servidor',
  ilegible: 'Respuesta ilegible',
}

/** Pantalla de los estados que no son `listo` (contracts/api-lectura.md §Errores que el front distingue). */
export default function EstadoCarga({ estado, reintentar }: Props) {
  const boton = (
    <button type="button" className="btn" onClick={reintentar}>
      Reintentar
    </button>
  )
  switch (estado.fase) {
    case 'cargando':
      return (
        <p className="estado estado-info" role="status">
          Cargando…
        </p>
      )
    case 'despertando':
      return (
        <div className="estado estado-info" role="status">
          <p className="estado-titulo">Despertando el servidor…</p>
          <p className="estado-detalle">
            La API gratuita se duerme sin uso y tarda hasta un minuto en arrancar. Sigo esperando la respuesta.
          </p>
        </div>
      )
    case 'sin_datos':
      return (
        <div className="estado estado-aviso" role="status">
          <p className="estado-titulo">Sin datos todavía</p>
          <p className="estado-detalle">
            La API responde, pero aún no tiene listings. Ejecuta el scorer: cada lote envía su pasada a la API.
          </p>
          {boton}
        </div>
      )
    case 'error':
      return (
        <div className="estado estado-error" role="alert">
          <p className="estado-titulo">{TITULO[estado.tipo]}</p>
          <p className="estado-detalle">{estado.detalle}.</p>
          {estado.url && (
            <p className="estado-detalle">
              Dirección consultada: <code>{estado.url}</code>
            </p>
          )}
          {boton}
        </div>
      )
  }
}
