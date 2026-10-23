/** Pestaña «Favoritos»: anuncios guardados en este navegador (localStorage), también los retirados. */
import { useMemo } from 'react'
import ListingCard from '../components/ListingCard'
import { esRetirado } from '../domain/derivaciones'
import { textosNovedad } from '../domain/tarjetas'
import { useDatos } from '../state/datos'
import { useFavoritos } from '../state/favoritos'

export default function Favoritos() {
  const { listings } = useDatos()
  const { favoritos, quitar } = useFavoritos()
  const porUrl = useMemo(() => new Map(listings.map((l) => [l.url, l])), [listings])

  return (
    <>
      <h2 className="sr-only-vista">Favoritos</h2>
      {favoritos.length === 0 ? (
        <div className="aviso aviso-info" role="status">
          Aún no tienes favoritos. Pulsa la estrella ☆ de un anuncio para guardarlo. Los favoritos se
          guardan solo en este navegador: no hay cuenta ni se envían a ningún servidor, y no se
          comparten con otros dispositivos.
        </div>
      ) : (
        <>
          <div className="lc-contador">
            {favoritos.length}
            <span>{favoritos.length === 1 ? 'favorito' : 'favoritos'} guardados en este navegador</span>
          </div>
          {favoritos.map((url) => {
            const l = porUrl.get(url)
            if (!l) {
              return (
                <div className="prop-card fav-huerfano" key={url}>
                  <div className="lc-cuerpo">
                    <div className="prop-title">Anuncio que ya no está en los datos</div>
                    <div className="prop-meta">{url}</div>
                  </div>
                  <button type="button" className="prop-action-btn" style={{ marginTop: 0 }} onClick={() => quitar(url)}>
                    Quitar de favoritos
                  </button>
                </div>
              )
            }
            const { meta, detalles, precio } = textosNovedad(l)
            return (
              <ListingCard
                key={url}
                variante="compacta"
                listing={l}
                lineas={[meta, detalles]}
                precio={<div className="lc-precio">{precio}</div>}
                extra={
                  esRetirado(l) ? (
                    <span className="lt-tag lt-usada" title="Sin apariciones recientes en el scraping">
                      retirado
                    </span>
                  ) : undefined
                }
              />
            )
          })}
        </>
      )}
    </>
  )
}
