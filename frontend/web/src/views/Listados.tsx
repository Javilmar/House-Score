import { memo, useMemo, useState } from 'react'
import Breakdown from '../components/Breakdown'
import BotonFavorito from '../components/BotonFavorito'
import Multiselect from '../components/Multiselect'
import SliderRango from '../components/SliderRango'
import { colorDias, diasEnMercado, esRetirado, fmtEur, agruparMiles, redondear, scoreColor } from '../domain/derivaciones'
import { generarCsv, nombreCsv } from '../domain/csv'
import {
  aplicarFiltros,
  enriquecer,
  fuenteDe,
  ordenar,
  paramsDeFiltros,
  resolverFiltros,
  scoreFinito,
  tituloDe,
  type Columna,
  type Direccion,
  type Fila,
  type Filtros,
} from '../domain/filtros'
import { paramsHipoteca } from '../domain/tarjetas'
import { useDatos } from '../state/datos'
import { useRuta, navegar as navegarRuta } from '../state/router'
import '../styles/listados.css'

const MEDALLAS = ['🥇', '🥈', '🥉']
/** El botón ↗ solo existe si el listing está entre los N máximos del slider de Top scoring (app.py:1401). */
const RANK_MAX_TOP = 30

const CABECERAS: { col: Columna; texto: string; titulo?: string }[] = [
  { col: 'titulo', texto: 'Título' },
  { col: 'precio', texto: 'Precio' },
  { col: 'score', texto: 'Score' },
  { col: 'eur_m2', texto: '€/m²' },
  { col: 'm2', texto: 'm²' },
  { col: 'tipo', texto: 'Tipo' },
  { col: 'fuente', texto: 'Fuente' },
  { col: 'ubicacion', texto: 'Ubicación' },
  { col: 'dias', texto: 'Días', titulo: 'Días en mercado' },
]

function claseFuente(fuente: string): string {
  if (fuente.includes('pisos')) return 'lt-src lt-src-pisos'
  if (fuente.includes('fotocasa')) return 'lt-src lt-src-fotocasa'
  return 'lt-src'
}

interface PropsFila {
  fila: Fila
  /** Posición en el orden inicial (score descendente): determina la medalla. */
  pos: number
  hoy: string
}

const FilaListado = memo(function FilaListado({ fila, pos, hoy }: PropsFila) {
  const { l } = fila
  const titulo = tituloDe(l)
  const enlazable = typeof l.url === 'string' && l.url.startsWith('http')
  const sc = scoreFinito(l)
  const dias = diasEnMercado(l.first_seen, hoy)
  const fuente = fuenteDe(l)
  const precio = Math.trunc(l.price || 0)

  return (
    <tr>
      <td className="lt-pos">{MEDALLAS[pos] ?? ''}</td>
      <td className="lt-title">
        {esRetirado(l) && (
          <>
            <span className="lt-tag lt-usada" title="Sin apariciones recientes en el scraping">
              retirado
            </span>{' '}
          </>
        )}
        {l.datos_insuficientes && (
          <>
            <span className="lt-tag lt-usada" title="Sin m² fiable: no valorado">
              s/valorar
            </span>{' '}
          </>
        )}
        {enlazable ? (
          <a href={l.url} target="_blank" rel="noopener">
            {titulo}
          </a>
        ) : (
          <span>{titulo}</span>
        )}
      </td>
      <td className="lt-price">{fmtEur(l.price)}</td>
      <td>
        <div className="lt-score-wrap">
          <span className="lt-score-num">{redondear(sc)}</span>
          <span className="lt-score-track">
            <span className="lt-score-fill" style={{ width: `${Math.min(sc, 100)}%`, background: scoreColor(sc) }} />
          </span>
        </div>
        <Breakdown listing={l} diferido />
      </td>
      <td className="lt-num">{fmtEur(l.eur_m2)}</td>
      <td className="lt-num">{Number.isFinite(l.m2) ? Math.trunc(l.m2) : '—'}</td>
      <td>
        <span className={`lt-tag ${fila.tipo === 'Obra nueva' ? 'lt-nuevo' : 'lt-usada'}`}>{fila.tipo}</span>
      </td>
      <td>
        <span className={claseFuente(fuente)}>{fuente || '—'}</span>
      </td>
      <td>{fila.zona}</td>
      <td className="lt-num" style={{ color: colorDias(dias), whiteSpace: 'nowrap' }}>
        {dias !== null ? `${dias}d` : '—'}
      </td>
      <td className="lt-acciones">
        <div className="lt-acciones-col">
          <BotonFavorito listing={l} />
          {fila.rank >= 0 && fila.rank < RANK_MAX_TOP && (
            <button
              type="button"
              className="lt-goto-btn"
              title="Ver en Top scoring"
              aria-label="Ver en Top scoring"
              onClick={() => navegarRuta('top', { id: l.url })}
            >
              ↗
            </button>
          )}
          <button
            type="button"
            className="lt-goto-btn"
            title="Calcular hipoteca"
            aria-label="Calcular hipoteca"
            onClick={() =>
              navegarRuta('hipoteca', paramsHipoteca(precio, fila.tipo, fila.zona))
            }
          >
            €
          </button>
        </div>
      </td>
    </tr>
  )
})

function descargarCsv(filas: Fila[], hoy: string) {
  const blob = new Blob([generarCsv(filas.map((f) => f.l))], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = nombreCsv(hoy)
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

/** Pestaña "Listados completos" (app.py:1197-1471). Los filtros viven en el hash. */
export default function Listados() {
  const { listings, hoy } = useDatos()
  const { params, setParams } = useRuta()
  const [orden, setOrden] = useState<{ col: Columna; dir: Direccion } | null>(null)

  const todas = useMemo(() => enriquecer(listings), [listings])
  const { base, filtros, opciones } = useMemo(() => resolverFiltros(todas, params), [todas, params])
  const filtradas = useMemo(() => aplicarFiltros(base, filtros), [base, filtros])
  const posiciones = useMemo(() => new Map(filtradas.map((f, i) => [f, i])), [filtradas])
  const visibles = useMemo(
    () => (orden ? ordenar(filtradas, orden.col, orden.dir, hoy) : filtradas),
    [filtradas, orden, hoy],
  )

  const cambiar = (parcial: Partial<Filtros>) => setParams(paramsDeFiltros({ ...filtros, ...parcial }, opciones))

  const ordenarPor = (col: Columna) =>
    setOrden((o) => ({ col, dir: o?.col === col && o.dir === 'asc' ? 'desc' : 'asc' }))

  return (
    <>
      <h2 className="sr-only-vista">Listados completos</h2>

      <label className="f-check">
        <input
          type="checkbox"
          checked={filtros.retirados}
          onChange={(e) => cambiar({ retirados: e.target.checked })}
        />
        Mostrar retirados
      </label>

      <div className="f-fila f-fila-4">
        <Multiselect
          etiqueta="Zona"
          opciones={opciones.zonas}
          valor={filtros.zonas}
          onChange={(zonas) => cambiar({ zonas })}
        />
        <Multiselect
          etiqueta="Municipio"
          opciones={opciones.municipios}
          valor={filtros.municipios}
          onChange={(municipios) => cambiar({ municipios })}
        />
        <SliderRango
          etiqueta="Rango de score"
          min={opciones.score[0]}
          max={opciones.score[1]}
          valor={filtros.score}
          onChange={(score) => cambiar({ score })}
        />
        {opciones.precio && filtros.precio && (
          <SliderRango
            etiqueta="Rango de precio (€)"
            min={opciones.precio[0]}
            max={opciones.precio[1]}
            step={1000}
            valor={filtros.precio}
            onChange={(precio) => cambiar({ precio })}
            formato={(n) => `${agruparMiles(n, ',')} €`}
          />
        )}
      </div>
      <div className="f-fila f-fila-hab">
        {opciones.hab && filtros.hab && (
          <SliderRango
            etiqueta="Habitaciones"
            min={opciones.hab[0]}
            max={opciones.hab[1]}
            valor={filtros.hab}
            onChange={(hab) => cambiar({ hab })}
          />
        )}
      </div>

      {visibles.length > 0 ? (
        <div className="list-table-wrap scroll" style={{ maxHeight: Math.min(660, 64 + visibles.length * 41) }}>
          <table className="list-table">
            <thead>
              <tr>
                <th className="noord" />
                {CABECERAS.map(({ col, texto, titulo }) => {
                  const activa = orden?.col === col
                  return (
                    <th
                      key={col}
                      className="sortable"
                      title={titulo}
                      tabIndex={0}
                      aria-sort={activa ? (orden.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                      onClick={() => ordenarPor(col)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          ordenarPor(col)
                        }
                      }}
                    >
                      {texto}
                      <span className="arr">{activa ? (orden.dir === 'asc' ? ' ▲' : ' ▼') : ''}</span>
                    </th>
                  )
                })}
                <th className="noord" style={{ width: 38 }} title="Ver en Top scoring" />
              </tr>
            </thead>
            <tbody>
              {visibles.map((f) => (
                <FilaListado key={f.l.url} fila={f} pos={posiciones.get(f)!} hoy={hoy} />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="aviso aviso-info" role="status">
          No hay listados con esos filtros.
        </div>
      )}

      <p className="caption">
        {filtradas.length} listings · clic en una cabecera para ordenar · clic en el título para abrir el anuncio
      </p>
      <button type="button" className="btn" onClick={() => descargarCsv(filtradas, hoy)}>
        Descargar CSV
      </button>
    </>
  )
}
