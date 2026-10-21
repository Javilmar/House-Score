import type { ReactNode } from 'react'
import { clean, redondear } from '../domain/derivaciones'
import { fmtComa, descripcionTarjeta, metaTop, paramsHipotecaTarjeta } from '../domain/tarjetas'
import { parseScoreDetails } from '../domain/desglose'
import { navegar } from '../state/router'
import type { Listing } from '../types'
import Breakdown from './Breakdown'
import Icon from './Icon'
import ScoreBadge, { ScoreBar } from './ScoreBadge'
import '../styles/listing-card.css'

const tituloDe = (l: Pick<Listing, 'title'>) => clean(String(l.title ?? '')) || 'Sin título'
const scoreDe = (l: Pick<Listing, 'score'>) => (Number.isFinite(l.score) ? l.score : 0)

/** Título: enlace si la url empieza por http; si no, texto (app.py:1485-1494). */
function Titulo({ l }: { l: Listing }) {
  return typeof l.url === 'string' && l.url.startsWith('http') ? (
    <a className="prop-title" href={l.url} target="_blank" rel="noopener">
      {tituloDe(l)}
    </a>
  ) : (
    <span className="prop-title">{tituloDe(l)}</span>
  )
}

/** Botón `€ Hipoteca`: abre `#/hipoteca` con precio, tipo y CCAA precargados. */
function BotonHipoteca({ l }: { l: Listing }) {
  return (
    <button type="button" className="prop-action-btn hip-btn" onClick={() => navegar('hipoteca', paramsHipotecaTarjeta(l))}>
      € Hipoteca
    </button>
  )
}

interface PropsComunes {
  listing: Listing
}

interface PropsCompleta extends PropsComunes {
  variante: 'completa'
  /** Posición 0-based en el orden por score: `id="card-{i}"` y el número de rank. */
  indice: number
  resaltada?: boolean
}

interface PropsCompacta extends PropsComunes {
  variante: 'compacta'
  /** Líneas bajo el título (`.prop-meta`); la segunda lleva el margen de app.py:1918. */
  lineas: string[]
  /** Columna derecha (precio). */
  precio: ReactNode
  /** Elemento extra tras el precio (badge de % de Bajadas). */
  extra?: ReactNode
}

/**
 * Tarjeta de listado compartida por Top scoring (`completa`, app.py:1556-1583),
 * Bajadas de precio y Novedades (`compacta`, app.py:1775-1799 y 1910-1928).
 */
export default function ListingCard(props: PropsCompleta | PropsCompacta) {
  const l = props.listing
  if (props.variante === 'compacta') {
    return (
      <div className="prop-card">
        <div className="lc-fila-compacta">
          <ScoreBadge score={scoreDe(l)} />
          <div className="lc-cuerpo">
            <div>
              <Titulo l={l} />
            </div>
            {props.lineas.map((t, i) => (
              <div className="prop-meta" key={i} style={i > 0 ? { marginTop: '0.15rem' } : undefined}>
                {t}
              </div>
            ))}
          </div>
          <div className="lc-precio-compacto">{props.precio}</div>
          {props.extra}
        </div>
        <BotonHipoteca l={l} />
      </div>
    )
  }

  const { indice, resaltada } = props
  const score = scoreDe(l)
  const { features, penalties } = parseScoreDetails(l)
  const descripcion = descripcionTarjeta(l.description)
  return (
    <div className={`prop-card${resaltada ? ' prop-card-resaltada' : ''}`} id={`card-${indice}`} style={{ scrollMarginTop: '80px' }}>
      <div className="prop-card-row">
        <ScoreBadge score={score} />
        <div className="prop-card-body">
          <div>
            <span className="prop-rank">{indice + 1}.</span> <Titulo l={l} />
          </div>
          <div className="prop-meta">
            {metaTop(l).map(([ic, texto]) => (
              <span className="meta-item" key={ic}>
                <Icon name={ic} size={15} />
                {texto}
              </span>
            ))}
          </div>
          <ScoreBar score={score} />
        </div>
        <div className="prop-price">
          <div className="lc-precio">{fmtComa(l.price)} €</div>
          <div className="lc-eur-m2">{fmtComa(l.eur_m2 ?? 0)} €/m²</div>
          <div className="lc-fila-atributos">
            <span className="meta-item">
              <Icon name="ruler" size={14} />
              {redondear(l.m2)} m²
            </span>
            <span className="meta-item">
              <Icon name="bed" size={14} />
              {redondear(l.rooms)}
            </span>
            <span className="meta-item">
              <Icon name="bath" size={14} />
              {redondear(l.bathrooms)}
            </span>
          </div>
        </div>
      </div>
      <div style={{ marginTop: '0.75rem' }}>
        {features.map((c, i) => (
          <span className="chip" key={`f${i}`}>
            {c}
          </span>
        ))}
        {penalties.map((p, i) => (
          <span className="chip chip-warn" key={`p${i}`}>
            {p}
          </span>
        ))}
      </div>
      <Breakdown listing={l} />
      {descripcion && (
        <details className="score-breakdown lc-descripcion">
          <summary>Descripción</summary>
          <p>{descripcion}</p>
        </details>
      )}
      <BotonHipoteca l={l} />
    </div>
  )
}
