interface Props {
  /** Momento en que el navegador recibió los datos. */
  cargadoEn: Date
  /** URL de la API configurada. */
  url: string
  /** Vuelve a pedir los datos a la API. */
  onRecargar: () => void
}

const dos = (n: number) => String(n).padStart(2, '0')

/** `strftime('%Y-%m-%d %H:%M:%S')` en hora local. */
export const fechaHora = (d: Date) =>
  `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())} ${dos(d.getHours())}:${dos(d.getMinutes())}:${dos(d.getSeconds())}`

/** Pie de página de app.py:2716-2724: divisor y `st.caption` con la última actualización. */
export default function PiePagina({ cargadoEn, url, onRecargar }: Props) {
  return (
    <footer>
      <hr />
      <p className="caption pie">
        Última actualización: {fechaHora(cargadoEn)} · Datos de la API en <code>{url}</code> ·{' '}
        <a
          href="?rerun"
          onClick={(e) => {
            e.preventDefault()
            onRecargar()
          }}
        >
          Forzar recarga
        </a>{' '}
        · Scorer: property_scorer_all.py (pisos.com + fotocasa · Madrid Sur, Este, Sureste y Norte + Toledo Norte · ≤ 300.000–400.000 € según zona)
      </p>
    </footer>
  )
}
