import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../../src/App'
import { historicoApi, listingsApi } from '../fixtures'

const json = (c: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(c), { status }))

beforeEach(() => window.history.replaceState(null, '', '/'))

describe('App: cabecera de KPI', () => {
  it('muestra los 6 KPI sobre las pestañas cuando hay datos', async () => {
    const f = vi.fn((url: string | URL | Request) =>
      json(String(url).includes('/historico') ? historicoApi() : listingsApi()),
    ) as unknown as typeof fetch
    const { container } = render(<App opciones={{ apiUrl: 'http://api.test', fetchFn: f }} hoy="2026-07-21" />)
    await screen.findByRole('tablist')
    const kpis = container.querySelector('.kpi-grid')!
    expect(kpis.querySelectorAll('.kpi-card')).toHaveLength(6)
    expect(kpis.compareDocumentPosition(screen.getByRole('tablist')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    const activos = listingsApi().filter((l) => l.estado === 'activo').length
    expect(kpis.querySelector('.kpi-value')!.textContent).toBe(String(activos))
  })

  it('en error no hay KPI ni cifras', async () => {
    const f = vi.fn(() => json({}, 503)) as unknown as typeof fetch
    const { container } = render(<App opciones={{ apiUrl: 'http://api.test', fetchFn: f }} hoy="2026-07-21" />)
    await screen.findByRole('alert')
    expect(container.querySelector('.kpi-grid')).toBeNull()
  })
})
