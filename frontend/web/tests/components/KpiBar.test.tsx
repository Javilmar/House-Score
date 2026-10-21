import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import KpiBar from '../../src/components/KpiBar'
import { DatosProvider } from '../../src/state/datos'
import { listing } from '../helpers'

describe('<KpiBar>', () => {
  it('6 tarjetas con icono, etiqueta y valor en el orden de app.py', () => {
    const ls = [listing({ price: 100000, score: 80, first_seen: '2026-07-21' }), listing({ price: 200000, score: 60, status: 'delisted', price_drop: 10 })]
    const { container } = render(
      <DatosProvider listings={ls} historico={[]} hoy="2026-07-21">
        <KpiBar />
      </DatosProvider>,
    )
    const tarjetas = [...container.querySelectorAll('.kpi-grid > .kpi-card')]
    expect(tarjetas).toHaveLength(6)
    expect(tarjetas.map((t) => t.querySelector('.kpi-label')!.textContent)).toEqual([
      'Total listings', 'Nuevos hoy', 'Score medio', 'Precio medio', 'Bajadas', 'Sin valorar',
    ])
    expect(tarjetas.map((t) => t.querySelector('.kpi-value')!.textContent)).toEqual(['1', '1', '70.0', '150,000 €', '1', '0'])
    for (const t of tarjetas) expect(t.querySelector('.kpi-icon svg')).not.toBeNull()
  })
})
