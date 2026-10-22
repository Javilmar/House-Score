import { Fragment, useEffect, useMemo, useState, type ReactNode } from 'react'
import Grafico from '../components/Grafico'
import {
  agregarPrecios,
  capaActiva,
  capasDisponibles,
  figuraCriminalidad,
  figuraPrecio,
  figuraRenta,
  leerCriminalidad,
  leerSecciones,
  notaCriminalidad,
  notaPrecio,
  notaRenta,
  rankingCriminalidad,
  rankingPrecio,
  rankingRenta,
  sinDatoCriminalidad,
  type CapaId,
  type FilaCriminalidad,
  type FilaSeccion,
  type GeoJson,
} from '../domain/mapas'
import { useDatos } from '../state/datos'
import { useRuta } from '../state/router'
import '../styles/mapas.css'

interface Assets {
  geojsonMun: GeoJson | null
  criminalidad: FilaCriminalidad[]
  geojsonSec: GeoJson | null
  renta: FilaSeccion[]
}

const BASE = import.meta.env.BASE_URL

async function pedir(nombre: string): Promise<string | null> {
  try {
    const r = await fetch(`${BASE}assets/${nombre}`)
    return r.ok ? await r.text() : null
  } catch {
    return null
  }
}

async function pedirGeoJson(nombre: string): Promise<GeoJson | null> {
  const texto = await pedir(nombre)
  if (texto === null) return null
  try {
    const gj = JSON.parse(texto) as GeoJson
    return Array.isArray(gj.features) ? gj : null
  } catch {
    return null
  }
}

/** Descarga los tres assets (solo al montar la vista) y los convierte en filas. */
async function cargarAssets(): Promise<Assets> {
  const [geojsonMun, csv, geojsonSec] = await Promise.all([
    pedirGeoJson('municipios_zona.geojson'),
    pedir('criminalidad.csv'),
    pedirGeoJson('secciones_renta.geojson'),
  ])
  return {
    geojsonMun,
    criminalidad: csv === null ? [] : leerCriminalidad(csv),
    geojsonSec,
    renta: geojsonSec === null ? [] : leerSecciones(geojsonSec),
  }
}

const AVISO_BUILD = 'python frontend/scripts/build_mapa_assets.py'

function Aviso({ texto }: { texto: string }) {
  return (
    <div className="aviso" role="alert">
      <p>{texto}</p>
      <pre>{AVISO_BUILD}</pre>
    </div>
  )
}

/** Markdown mínimo de `st.caption`: solo `**negrita**`. */
function Nota({ texto }: { texto: string }) {
  const partes: ReactNode[] = texto.split('**').map((t, i) => (i % 2 ? <strong key={i}>{t}</strong> : <Fragment key={i}>{t}</Fragment>))
  return <p className="caption">{partes}</p>
}

function Tabla({ filas }: { filas: Record<string, string | number>[] }) {
  const columnas = Object.keys(filas[0] ?? {})
  return (
    <div className="list-table-wrap scroll mapas-tabla">
      <table className="list-table">
        <thead>
          <tr>
            <th className="noord" />
            {columnas.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((f, i) => (
            <tr key={i}>
              <td className="lt-pos">{i + 1}</td>
              {columnas.map((c) => (
                <td key={c}>{f[c]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function VistaCriminalidad({ filas, geojson }: { filas: FilaCriminalidad[]; geojson: GeoJson }) {
  const figura = useMemo(() => figuraCriminalidad(filas, geojson), [filas, geojson])
  const sinDato = useMemo(() => sinDatoCriminalidad(filas, geojson), [filas, geojson])
  const ranking = useMemo(() => rankingCriminalidad(filas), [filas])
  const periodo = filas[0]?.periodo ?? 'Q1 2026'
  return (
    <>
      <Grafico data={figura.data} layout={figura.layout} />
      <Nota texto={notaCriminalidad(periodo)} />
      <details className="expander">
        <summary>{`Municipios sin datos oficiales (${sinDato.length} en gris)`}</summary>
        <div className="expander-body">
          <p>{sinDato.length > 0 ? sinDato.join(', ') : 'Todos tienen datos.'}</p>
        </div>
      </details>
      <h3>Ranking de peligrosidad</h3>
      <Tabla filas={ranking} />
    </>
  )
}

function VistaRenta({ filas, geojson }: { filas: FilaSeccion[]; geojson: GeoJson }) {
  const figura = useMemo(() => figuraRenta(filas, geojson), [filas, geojson])
  const ranking = useMemo(() => rankingRenta(filas), [filas])
  const sinRenta = useMemo(
    () =>
      filas
        .filter((f) => f.renta_persona === null)
        .map((f) => ({ Municipio: f.municipio, cusec: f.cusec }))
        .sort((a, b) => a.Municipio.localeCompare(b.Municipio)),
    [filas],
  )
  return (
    <>
      <Grafico data={figura.data} layout={figura.layout} />
      <Nota texto={notaRenta(filas[0]?.anio ?? '2023', sinRenta.length)} />
      {sinRenta.length > 0 && (
        <details className="expander">
          <summary>{`Secciones sin dato de renta (${sinRenta.length} en gris)`}</summary>
          <div className="expander-body">
            <div className="list-table-wrap scroll mapas-tabla">
              <table className="list-table">
                <thead>
                  <tr>
                    <th>municipio</th>
                    <th>cusec</th>
                  </tr>
                </thead>
                <tbody>
                  {sinRenta.map((f) => (
                    <tr key={f.cusec}>
                      <td>{f.Municipio}</td>
                      <td>{f.cusec}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </details>
      )}
      <h3>Ranking de barrios por renta</h3>
      <Tabla filas={ranking} />
    </>
  )
}

function VistaPrecio({ geojson }: { geojson: GeoJson | null }) {
  const { listings } = useDatos()
  const filas = useMemo(() => (geojson ? agregarPrecios(listings, geojson) : []), [listings, geojson])
  const figura = useMemo(() => (geojson ? figuraPrecio(filas, geojson) : null), [filas, geojson])
  const ranking = useMemo(() => rankingPrecio(filas), [filas])
  if (geojson === null || figura === null) {
    return <Aviso texto="GeoJSON de municipios no encontrado. Ejecuta el script de build:" />
  }
  return (
    <>
      <Grafico data={figura.data} layout={figura.layout} />
      <Nota texto={notaPrecio(geojson.features.length - filas.length)} />
      <h3>Ranking de precio por municipio</h3>
      <Tabla filas={ranking} />
    </>
  )
}

export default function Mapas() {
  const { params, setParams } = useRuta()
  const [assets, setAssets] = useState<Assets | null>(null)

  useEffect(() => {
    let vivo = true
    void cargarAssets().then((a) => {
      if (vivo) setAssets(a)
    })
    return () => {
      vivo = false
    }
  }, [])

  let cuerpo: ReactNode
  if (assets === null) {
    cuerpo = (
      <p role="status" className="caption">
        Cargando mapas…
      </p>
    )
  } else {
    const tieneCriminalidad = assets.geojsonMun !== null && assets.criminalidad.length > 0
    const tieneRenta = assets.geojsonSec !== null && assets.renta.length > 0
    if (!tieneCriminalidad && !tieneRenta) {
      cuerpo = <Aviso texto="Activos del mapa no encontrados. Ejecuta primero el script de build:" />
    } else {
      const capas = capasDisponibles(tieneCriminalidad, tieneRenta)
      const capa: CapaId = capaActiva(capas, params.capa)
      cuerpo = (
        <>
          <div className="radio-capa" role="radiogroup" aria-label="Capa">
            {capas.map((c) => (
              <label key={c.id} className="radio-opcion">
                <input
                  type="radio"
                  name="capa"
                  value={c.id}
                  checked={capa === c.id}
                  onChange={() => setParams({ capa: c.id })}
                />
                <span>{c.etiqueta}</span>
              </label>
            ))}
          </div>
          {capa === 'criminalidad' && assets.geojsonMun && <VistaCriminalidad filas={assets.criminalidad} geojson={assets.geojsonMun} />}
          {capa === 'renta' && assets.geojsonSec && <VistaRenta filas={assets.renta} geojson={assets.geojsonSec} />}
          {capa === 'precio' && <VistaPrecio geojson={assets.geojsonMun} />}
        </>
      )
    }
  }

  return (
    <section className="mapas">
      <h2 className="sr-only-vista">Mapas</h2>
      {cuerpo}
    </section>
  )
}
