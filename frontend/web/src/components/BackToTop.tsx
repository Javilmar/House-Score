import { useEffect, useState } from 'react'

/** Scroll (px) a partir del cual aparece el botón (app.py:955). */
const UMBRAL_PX = 300

/** Botón flotante «volver arriba» (app.py:931-960): visible tras 300 px de scroll, sube con scroll suave. */
export default function BackToTop() {
  const [visible, setVisible] = useState(() => window.scrollY > UMBRAL_PX)
  useEffect(() => {
    const alScroll = () => setVisible(window.scrollY > UMBRAL_PX)
    window.addEventListener('scroll', alScroll, { passive: true })
    return () => window.removeEventListener('scroll', alScroll)
  }, [])
  if (!visible) return null
  return (
    <button
      type="button"
      className="back-top"
      title="Volver arriba"
      aria-label="Volver arriba"
      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
    >
      ↑
    </button>
  )
}
