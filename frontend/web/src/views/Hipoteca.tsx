/** Pestaña «Hipoteca» (app.py `with tab6:`, 1937-2144). */
import { useId, useState } from 'react'
import Icon from '../components/Icon'
import Slider from '../components/Slider'
import { calcHipoteca, eur, esfuerzo } from '../domain/hipoteca'
import { useDatos } from '../state/datos'
import { useRuta } from '../state/router'
import '../styles/expander.css'
import '../styles/hipoteca.css'

const TIPOS = ['Segunda mano', 'Obra nueva'] as const
const CCAAS = ['Comunidad de Madrid', 'Castilla-La Mancha'] as const
const TIPO_RUTA: Record<string, (typeof TIPOS)[number]> = {
  'segunda-mano': 'Segunda mano',
  'obra-nueva': 'Obra nueva',
}
const CCAA_RUTA: Record<string, (typeof CCAAS)[number]> = {
  madrid: 'Comunidad de Madrid',
  clm: 'Castilla-La Mancha',
}

const PRECIO_MIN = 10_000
const PRECIO_MAX = 5_000_000
const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v))

/** int(df["price"].median()) con 200000 si no hay precios (app.py:1941-1945). */
function precioMedio(precios: number[]): number {
  const v = precios.filter((p) => p > 0).sort((a, b) => a - b)
  if (v.length === 0) return 200000
  const m = v.length >> 1
  return Math.trunc(v.length % 2 ? (v[m] ?? 0) : ((v[m - 1] ?? 0) + (v[m] ?? 0)) / 2)
}

const primero = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v)

function Numero(props: {
  etiqueta: string
  min: number
  max: number
  step: number
  value: number
  onChange: (v: number) => void
}) {
  const id = useId()
  const { etiqueta, min, max, step, value, onChange } = props
  return (
    <div className="hip-campo">
      <label htmlFor={id}>{etiqueta}</label>
      <div className="st-num">
        <input
          id={id}
          type="number"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => {
            const n = e.target.valueAsNumber
            if (Number.isFinite(n)) onChange(n)
          }}
          onBlur={() => onChange(clamp(value, min, max))}
        />
        <button
          type="button"
          aria-label="Disminuir"
          disabled={value <= min}
          onClick={() => onChange(clamp(value - step, min, max))}
        >
          <svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor" aria-hidden="true">
            <path d="M0 3h8v2H0z" />
          </svg>
        </button>
        <button
          type="button"
          aria-label="Aumentar"
          disabled={value >= max}
          onClick={() => onChange(clamp(value + step, min, max))}
        >
          <svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor" aria-hidden="true">
            <path d="M3 0h2v3h3v2H5v3H3V5H0V3h3z" />
          </svg>
        </button>
      </div>
    </div>
  )
}

function Opciones<T extends string>(props: {
  nombre: string
  opciones: readonly T[]
  value: T
  onChange: (v: T) => void
}) {
  return (
    <fieldset className="hip-radios">
      <legend>{props.nombre}</legend>
      <div className="hip-radios-fila">
        {props.opciones.map((o) => (
          <label key={o}>
            <input
              type="radio"
              name={props.nombre}
              checked={props.value === o}
              onChange={() => props.onChange(o)}
            />
            {o}
          </label>
        ))}
      </div>
    </fieldset>
  )
}

export default function Hipoteca() {
  const { activos } = useDatos()
  const { params } = useRuta()

  const pRuta = Number.parseInt(primero(params.precio) ?? '', 10)
  const tRuta = TIPO_RUTA[primero(params.tipo) ?? '']
  const cRuta = CCAA_RUTA[primero(params.ccaa) ?? '']
  // Equivalente a `hip_nav_id`: cada navegación distinta precarga una vez; las ediciones no se pisan.
  const claveRuta = `${params.precio ?? ''}|${params.tipo ?? ''}|${params.ccaa ?? ''}`

  const [precio, setPrecio] = useState(() =>
    Number.isFinite(pRuta) ? clamp(pRuta, PRECIO_MIN, PRECIO_MAX) : precioMedio(activos.map((l) => l.price)),
  )
  const [tipo, setTipo] = useState<(typeof TIPOS)[number]>(tRuta ?? 'Segunda mano')
  const [ccaa, setCcaa] = useState<(typeof CCAAS)[number]>(cRuta ?? 'Comunidad de Madrid')
  const [claveAplicada, setClaveAplicada] = useState(claveRuta)
  if (claveRuta !== claveAplicada) {
    setClaveAplicada(claveRuta)
    if (Number.isFinite(pRuta)) setPrecio(clamp(pRuta, PRECIO_MIN, PRECIO_MAX))
    if (tRuta) setTipo(tRuta)
    if (cRuta) setCcaa(cRuta)
  }

  const [entradaPct, setEntradaPct] = useState(20)
  const [plazo, setPlazo] = useState(30)
  const [tin, setTin] = useState(3)

  const [comunidad, setComunidad] = useState(80)
  const [ibi, setIbi] = useState(50)
  const [seguro, setSeguro] = useState(30)
  const [luz, setLuz] = useState(80)
  const [internet, setInternet] = useState(35)
  const [ingresos, setIngresos] = useState(2500)

  const esObraNueva = tipo === 'Obra nueva'
  const res = calcHipoteca(
    clamp(precio, PRECIO_MIN, PRECIO_MAX),
    entradaPct / 100,
    plazo,
    tin / 100,
    esObraNueva,
    ccaa,
  )
  const g = esfuerzo(res.cuota_mensual, comunidad + ibi + seguro + luz + internet, ingresos)

  const kpis: [string, string, string][] = [
    ['wallet', 'Cuota mensual', eur(res.cuota_mensual)],
    ['zap', 'Ahorro necesario', eur(res.ahorro_necesario)],
    ['trending-down', 'Total intereses', eur(res.total_intereses)],
    ['building', 'Total desembolso', eur(res.total_pagado)],
  ]
  const tipoTxt = esObraNueva ? 'Obra nueva (IVA + AJD)' : 'Segunda mano (ITP)'

  return (
    <div>
      <h2 className="sr-only-vista">Hipoteca</h2>
      <h3>Calculadora de hipoteca</h3>

      <div className="hip-cols">
        <div className="hip-col">
          <Numero
            etiqueta="Precio de compra (€)"
            min={PRECIO_MIN}
            max={PRECIO_MAX}
            step={5000}
            value={precio}
            onChange={setPrecio}
          />
          <div className="hip-precio">
            {String(Math.trunc(clamp(precio, PRECIO_MIN, PRECIO_MAX))).replace(/\B(?=(\d{3})+(?!\d))/g, '.')}
            <span className="hip-precio-eur">€</span>
          </div>
          <Opciones nombre="Tipo de vivienda" opciones={TIPOS} value={tipo} onChange={setTipo} />
          <Opciones nombre="Comunidad autónoma" opciones={CCAAS} value={ccaa} onChange={setCcaa} />
        </div>
        <div className="hip-col">
          <Slider
            etiqueta="Entrada (%)"
            min={5}
            max={50}
            step={1}
            value={entradaPct}
            onChange={setEntradaPct}
            formato={(v) => `${v}%`}
          />
          <Slider etiqueta="Plazo (años)" min={5} max={40} step={1} value={plazo} onChange={setPlazo} />
        </div>
        <div className="hip-col">
          <Slider
            etiqueta="Tipo de interés fijo (%)"
            min={0.5}
            max={8}
            step={0.05}
            value={tin}
            onChange={setTin}
            formato={(v) => `${v.toFixed(2)}%`}
          />
        </div>
      </div>

      <div className="hip-kpis">
        {kpis.map(([icono, etiqueta, valor]) => (
          <div className="kpi-card" key={etiqueta}>
            <div className="kpi-icon">
              <Icon name={icono} size={18} />
            </div>
            <div className="kpi-label">{etiqueta}</div>
            <div className="kpi-value">{valor}</div>
          </div>
        ))}
      </div>

      <p>
        <strong>Desglose de ahorro necesario:</strong>
      </p>
      <div className="hip-desglose">
        <table className="sb-table">
          <thead>
            <tr>
              <th>Concepto ({tipoTxt})</th>
              <th>Importe</th>
            </tr>
          </thead>
          <tbody>
            <tr className="sb-row">
              <td>Entrada ({entradaPct}%)</td>
              <td className="hip-importe">{eur(res.entrada)}</td>
            </tr>
            {res.impuestos.items.map(([etiqueta, importe]) => (
              <tr className="sb-row" key={etiqueta}>
                <td>{etiqueta}</td>
                <td className="hip-importe">{eur(importe)}</td>
              </tr>
            ))}
            <tr className="sb-row">
              <td>Otros gastos (gestoría, notaría, tasación…)</td>
              <td className="hip-importe">{eur(res.otros_gastos)}</td>
            </tr>
            <tr className="sb-total">
              <td>Ahorro necesario total</td>
              <td>{eur(res.ahorro_necesario)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p className="caption">
        Tipos impositivos orientativos 2026. ITP: C. Madrid 4% / CLM 9%. AJD (obra nueva): C. Madrid 0,75% /
        CLM 1,5%. IVA obra nueva: 10%. Otros gastos (~1,5% + tasación 400€) son estimaciones. Pueden existir
        bonificaciones por edad, familia numerosa, VPO, etc.
      </p>

      <details className="expander">
        <summary>Gastos mensuales estimados</summary>
        <div className="expander-body">
          <div className="hip-cols-2">
            <div className="hip-col">
              <Slider etiqueta="Comunidad (€/mes)" min={0} max={300} step={5} value={comunidad} onChange={setComunidad} />
              <Slider etiqueta="IBI mensual (€/mes)" min={0} max={200} step={5} value={ibi} onChange={setIbi} />
              <Slider etiqueta="Seguro hogar (€/mes)" min={0} max={150} step={5} value={seguro} onChange={setSeguro} />
            </div>
            <div className="hip-col">
              <Slider etiqueta="Luz + gas (€/mes)" min={0} max={250} step={5} value={luz} onChange={setLuz} />
              <Slider etiqueta="Internet (€/mes)" min={0} max={80} step={5} value={internet} onChange={setInternet} />
              <Numero
                etiqueta="Ingresos netos mensuales (€)"
                min={500}
                max={20000}
                step={100}
                value={ingresos}
                onChange={setIngresos}
              />
            </div>
          </div>
          <div className="hip-gastos">
            <div className="kpi-card">
              <div className="kpi-label">Coste mensual total</div>
              <div className="kpi-value">{eur(g.total)}</div>
              <div className="hip-gastos-nota">{`cuota ${eur(res.cuota_mensual)} + gastos ${eur(g.gastos)}`}</div>
            </div>
            <div className="kpi-card" style={{ background: g.bg, borderColor: g.border }}>
              <div className="kpi-label">Esfuerzo sobre ingresos</div>
              <div className="kpi-value" style={{ color: g.color }}>
                {g.ratio.toFixed(1)}%
              </div>
              <div className="hip-gastos-nota">recomendado &lt; 30 %</div>
            </div>
          </div>
        </div>
      </details>
    </div>
  )
}
