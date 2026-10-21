import EstadoCarga from './components/EstadoCarga'
import Icon from './components/Icon'
import KpiBar from './components/KpiBar'
import { DatosProvider } from './state/datos'
import { useCarga, type OpcionesCarga } from './state/carga'
import { useRuta, type Vista } from './state/router'
import Bajadas from './views/Bajadas'
import ComoFunciona from './views/ComoFunciona'
import Evolucion from './views/Evolucion'
import Hipoteca from './views/Hipoteca'
import Listados from './views/Listados'
import Mapas from './views/Mapas'
import Novedades from './views/Novedades'
import Top from './views/Top'
import type { ComponentType } from 'react'

/** Orden de app.py:1121; iconos de app.py:1150-1159. */
const PESTANAS: { vista: Vista; etiqueta: string; icono: string; Componente: ComponentType }[] = [
  { vista: 'listados', etiqueta: 'Listados completos', icono: 'layers', Componente: Listados },
  { vista: 'top', etiqueta: 'Top scoring', icono: 'star', Componente: Top },
  { vista: 'novedades', etiqueta: 'Novedades', icono: 'sparkles', Componente: Novedades },
  { vista: 'evolucion', etiqueta: 'Evolución y análisis', icono: 'waves', Componente: Evolucion },
  { vista: 'bajadas', etiqueta: 'Bajadas de precio', icono: 'trending-down', Componente: Bajadas },
  { vista: 'hipoteca', etiqueta: 'Hipoteca', icono: 'wallet', Componente: Hipoteca },
  { vista: 'como-funciona', etiqueta: 'Cómo funciona', icono: 'info', Componente: ComoFunciona },
  { vista: 'mapas', etiqueta: 'Mapas', icono: 'map-pin', Componente: Mapas },
]

function Pestanas({ vista, navegar }: Pick<ReturnType<typeof useRuta>, 'vista' | 'navegar'>) {
  const activa = PESTANAS.find((p) => p.vista === vista) ?? PESTANAS[0]!
  return (
    <>
      <div className="tabs" role="tablist">
        {PESTANAS.map((p) => (
          <button
            key={p.vista}
            type="button"
            role="tab"
            className="tab"
            aria-selected={p.vista === activa.vista}
            onClick={() => navegar(p.vista)}
          >
            <Icon name={p.icono} size={14} stroke={2} />
            {p.etiqueta}
          </button>
        ))}
      </div>
      <div role="tabpanel">
        <activa.Componente />
      </div>
    </>
  )
}

interface Props {
  /** Solo para tests: URL/fetch inyectables. */
  opciones?: OpcionesCarga
  /** Solo para tests: fecha de "hoy". */
  hoy?: string
}

export default function App({ opciones, hoy }: Props) {
  const { estado, reintentar } = useCarga(opciones)
  // El router vive en App para normalizar el hash desde el primer render, también durante la carga
  const { vista, navegar } = useRuta()
  return (
    <div className="block-container">
      <h1>House Score</h1>
      <p className="caption">
        Madrid Sur · Toledo Norte — pisos.com · idealista · Scoring a medida · Hasta 300.000 €
      </p>
      {estado.fase === 'listo' ? (
        <DatosProvider listings={estado.listings} historico={estado.historico} hoy={hoy}>
          <KpiBar />
          <Pestanas vista={vista} navegar={navegar} />
        </DatosProvider>
      ) : (
        <EstadoCarga estado={estado} reintentar={reintentar} />
      )}
    </div>
  )
}
