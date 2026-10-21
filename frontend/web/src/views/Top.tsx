/** Pestaña «Top scoring» (app.py `with tab2:`, 1473-1586). */
import { useEffect, useId, useMemo, useState } from 'react'
import ListingCard from '../components/ListingCard'
import { TOP_DEFECTO, TOP_MAX, TOP_MIN, topNDeParam } from '../domain/tarjetas'
import { useDatos } from '../state/datos'
import { useRuta } from '../state/router'

/** Duración del resaltado tras ↗ (app.py:517-520). */
const RESALTADO_MS = 1800

export default function Top() {
  const { listings } = useDatos()
  const { params, setParams } = useRuta()
  const idSlider = useId()
  const n = topNDeParam(params.n)
  const idListing = Array.isArray(params.id) ? params.id[0] : params.id
  const mostrados = useMemo(() => listings.slice(0, n), [listings, n])
  const indiceDestino = idListing === undefined ? -1 : mostrados.findIndex((l) => l.url === idListing)
  const [resaltada, setResaltada] = useState<number | null>(null)

  // goToCard: lleva la tarjeta a la vista y la resalta un momento
  useEffect(() => {
    if (indiceDestino < 0) return
    document.getElementById(`card-${indiceDestino}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setResaltada(indiceDestino)
    const t = setTimeout(() => setResaltada(null), RESALTADO_MS)
    return () => clearTimeout(t)
  }, [indiceDestino, idListing])

  return (
    <>
      <h2 className="sr-only-vista">Top scoring</h2>
      <div className="f-campo f-top">
        <label className="f-etiqueta" htmlFor={idSlider}>
          Mostrar top
        </label>
        <span className="f-valores">{n}</span>
        <input
          id={idSlider}
          type="range"
          min={TOP_MIN}
          max={TOP_MAX}
          step={1}
          value={n}
          onChange={(e) => setParams({ n: Number(e.target.value) === TOP_DEFECTO ? undefined : e.target.value })}
        />
      </div>
      {mostrados.map((l, i) => (
        <ListingCard key={l.url || i} variante="completa" listing={l} indice={i} resaltada={resaltada === i} />
      ))}
    </>
  )
}
