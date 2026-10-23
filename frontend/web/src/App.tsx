import BackToTop from './components/BackToTop'
import EstadoCarga from './components/EstadoCarga'
import Icon from './components/Icon'
import KpiBar from './components/KpiBar'
import PiePagina from './components/PiePagina'
import { API_URL } from './api/cliente'
import { DatosProvider } from './state/datos'
import { useCarga, type OpcionesCarga } from './state/carga'
import { useRuta, type Vista } from './state/router'
import Bajadas from './views/Bajadas'
import ComoFunciona from './views/ComoFunciona'
import Evolucion from './views/Evolucion'
import Favoritos from './views/Favoritos'
import Hipoteca from './views/Hipoteca'
import Listados from './views/Listados'
import Mapas from './views/Mapas'
import Novedades from './views/Novedades'
import Top from './views/Top'
import { useEffect, useMemo, useRef, type ComponentType } from 'react'

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
  { vista: 'favoritos', etiqueta: 'Favoritos', icono: 'star', Componente: Favoritos },
]

function Pestanas({ vista, navegar }: Pick<ReturnType<typeof useRuta>, 'vista' | 'navegar'>) {
  const activa = PESTANAS.find((p) => p.vista === vista) ?? PESTANAS[0]!
  const lista = useRef<HTMLDivElement>(null)
  // Con la fila desplazada (móvil), deja a la vista la pestaña activa como hace st.tabs
  useEffect(() => {
    const el = lista.current
    const tab = el?.querySelector<HTMLElement>('[aria-selected="true"]')
    if (!el || !tab) return
    const r = el.getBoundingClientRect()
    const t = tab.getBoundingClientRect()
    if (t.left < r.left) el.scrollLeft -= r.left - t.left
    else if (t.right > r.right) el.scrollLeft += t.right - r.right
  }, [activa.vista])
  return (
    <>
      <div className="tabs" role="tablist" ref={lista}>
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
  // Momento en que llegaron los datos (cada carga completada crea un estado nuevo)
  const cargadoEn = useMemo(() => new Date(), [estado.fase === 'listo' ? estado : null])
  return (
    <div className="block-container">
      <h1>House Score</h1>
      <p className="caption">
        Madrid Sur, Este, Sureste y Norte · Toledo Norte — pisos.com · fotocasa · Scoring a medida · Hasta 300.000–400.000 € según zona
      </p>
      {estado.fase === 'listo' ? (
        <DatosProvider listings={estado.listings} historico={estado.historico} hoy={hoy}>
          <KpiBar />
          <Pestanas vista={vista} navegar={navegar} />
          <PiePagina cargadoEn={cargadoEn} url={opciones?.apiUrl ?? API_URL} onRecargar={reintentar} />
        </DatosProvider>
      ) : (
        <EstadoCarga estado={estado} reintentar={reintentar} />
      )}
      <BackToTop />
    </div>
  )
}
