import { useMemo } from 'react'
import { calcularKpis } from '../domain/kpis'
import { useDatos } from '../state/datos'
import Icon from './Icon'

/** Los 6 KPI de la cabecera (app.py:1020-1035). */
export default function KpiBar() {
  const { listings, hoy } = useDatos()
  const kpis = useMemo(() => calcularKpis(listings, hoy), [listings, hoy])
  return (
    <div className="kpi-grid">
      {kpis.map((k) => (
        <div className="kpi-card" key={k.etiqueta}>
          <div className="kpi-icon">
            <Icon name={k.icono} size={18} />
          </div>
          <div className="kpi-label">{k.etiqueta}</div>
          <div className="kpi-value">{k.valor}</div>
        </div>
      ))}
    </div>
  )
}
