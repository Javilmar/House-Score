import { clean } from '../domain/derivaciones'
import { useFavoritos } from '../state/favoritos'
import type { Listing } from '../types'

/** Estrella para guardar/quitar un anuncio de favoritos (solo en este navegador). */
export default function BotonFavorito({ listing }: { listing: Pick<Listing, 'url' | 'title'> }) {
  const { esFavorito, alternar } = useFavoritos()
  const activo = esFavorito(listing.url)
  const titulo = clean(String(listing.title ?? '')) || 'Sin título'
  return (
    <button
      type="button"
      className={`fav-btn${activo ? ' fav-btn-on' : ''}`}
      aria-pressed={activo}
      aria-label={`${activo ? 'Quitar de favoritos' : 'Añadir a favoritos'}: ${titulo}`}
      title={activo ? 'Quitar de favoritos' : 'Añadir a favoritos'}
      onClick={() => alternar(listing.url)}
    >
      {activo ? '★' : '☆'}
    </button>
  )
}
