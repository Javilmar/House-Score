import { Fragment, useId, useRef, type CSSProperties, type KeyboardEvent, type PointerEvent } from 'react'
import type { Rango } from '../domain/filtros'
import { fraccion } from './Slider'

interface Props {
  etiqueta: string
  min: number
  max: number
  step?: number
  valor: Rango
  onChange: (valor: Rango) => void
  formato?: (n: number) => string
}

type Tirador = 0 | 1

const redondea = (n: number) => Math.round(n * 1e6) / 1e6

/** Slider de rango (st.slider con tupla): dos tiradores que no se cruzan, valores sobre ellos y extremos del recorrido. */
export default function SliderRango({ etiqueta, min, max, step = 1, valor, onChange, formato = String }: Props) {
  const id = useId()
  const pista = useRef<HTMLDivElement>(null)
  const activo = useRef<Tirador | null>(null)
  const desactivado = min >= max

  const acota = (n: number) => Math.min(max, Math.max(min, n))
  /** Emite el valor del tirador `t` acotado al otro tirador; sin cambio efectivo no emite. */
  const fija = (t: Tirador, n: number) => {
    const v = t === 0 ? Math.min(acota(n), valor[1]) : Math.max(acota(n), valor[0])
    if (v === valor[t]) return
    onChange(t === 0 ? [v, valor[1]] : [valor[0], v])
  }
  /** Primer valor de la rejilla del paso estrictamente por encima (dir 1) o por debajo (dir −1) de `v`; el máximo siempre es alcanzable. */
  const salto = (v: number, dir: 1 | -1, pasos: number) => {
    const k = redondea((v - min) / step)
    const destino = dir > 0 ? Math.floor(k) + pasos : Math.ceil(k) - pasos
    return acota(redondea(min + destino * step))
  }
  const desdePuntero = (clientX: number) => {
    const r = pista.current!.getBoundingClientRect()
    const f = r.width > 0 ? Math.min(1, Math.max(0, (clientX - r.left) / r.width)) : 0
    return acota(redondea(min + Math.round((f * (max - min)) / step) * step))
  }

  const teclado = (t: Tirador) => (e: KeyboardEvent<HTMLDivElement>) => {
    if (desactivado) return
    const v = valor[t]
    let n: number
    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowUp':
        n = salto(v, 1, 1)
        break
      case 'ArrowLeft':
      case 'ArrowDown':
        n = salto(v, -1, 1)
        break
      case 'PageUp':
        n = salto(v, 1, 10)
        break
      case 'PageDown':
        n = salto(v, -1, 10)
        break
      case 'Home':
        n = min
        break
      case 'End':
        n = max
        break
      default:
        return
    }
    e.preventDefault()
    fija(t, n)
  }

  const alPulsar = (e: PointerEvent<HTMLDivElement>) => {
    if (desactivado) return
    const n = desdePuntero(e.clientX)
    // el más cercano; en empate, el que deja libre al otro lado
    const t: Tirador =
      Math.abs(n - valor[0]) < Math.abs(n - valor[1]) ? 0 : Math.abs(n - valor[0]) > Math.abs(n - valor[1]) ? 1 : n < valor[0] ? 0 : 1
    activo.current = t
    e.currentTarget.setPointerCapture?.(e.pointerId)
    pista.current?.querySelectorAll<HTMLElement>('[role="slider"]')[t]?.focus()
    fija(t, n)
  }
  const alMover = (e: PointerEvent<HTMLDivElement>) => {
    if (activo.current === null) return
    fija(activo.current, desdePuntero(e.clientX))
  }
  const alSoltar = () => {
    activo.current = null
  }

  const estilo = { '--a': fraccion(valor[0], min, max), '--b': fraccion(valor[1], min, max) } as CSSProperties
  const tiradores: [Tirador, string, string][] = [
    [0, 'mínimo', '--a'],
    [1, 'máximo', '--b'],
  ]
  return (
    <div className="f-campo st-slider-campo">
      <span className="f-etiqueta" id={id}>
        {etiqueta}
      </span>
      <div className="st-slider st-slider-rango" style={estilo} data-desactivado={desactivado || undefined}>
        <div
          ref={pista}
          className="st-slider-pista"
          onPointerDown={alPulsar}
          onPointerMove={alMover}
          onPointerUp={alSoltar}
          onPointerCancel={alSoltar}
        >
          {tiradores.map(([t, nombre, p]) => (
            <Fragment key={nombre}>
              <span className="st-slider-valor" style={{ '--p': `var(${p})` } as CSSProperties}>
                {formato(valor[t])}
              </span>
              <div
                role="slider"
                className="st-slider-tirador"
                style={{ '--p': `var(${p})` } as CSSProperties}
                tabIndex={desactivado ? -1 : 0}
                aria-label={`${etiqueta} (${nombre})`}
                aria-valuemin={min}
                aria-valuemax={max}
                aria-valuenow={valor[t]}
                aria-valuetext={formato(valor[t])}
                aria-disabled={desactivado || undefined}
                onKeyDown={teclado(t)}
              />
            </Fragment>
          ))}
        </div>
        <div className="st-slider-extremos" aria-hidden="true">
          <span>{formato(min)}</span>
          <span>{formato(max)}</span>
        </div>
      </div>
    </div>
  )
}
