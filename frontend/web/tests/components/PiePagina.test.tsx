import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../../src/App'
import PiePagina from '../../src/components/PiePagina'
import { historicoApi, listingsApi } from '../fixtures'

const CODIGO_PIE =
  'Scorer: property_scorer_all.py (pisos.com + fotocasa · Madrid Sur + Toledo Norte · ≤ 300.000 €)'

describe('PiePagina (app.py:2716-2724)', () => {
  it('muestra fecha y hora locales, la URL de la API, "Forzar recarga" y el scorer', () => {
    const { container } = render(
      <PiePagina cargadoEn={new Date(2026, 9, 22, 9, 5, 7)} url="https://api.test" onRecargar={() => {}} />,
    )
    const pie = container.querySelector('.pie')!
    expect(pie.textContent).toBe(
      `Última actualización: 2026-10-22 09:05:07 · Datos de la API en https://api.test · Forzar recarga · ${CODIGO_PIE}`,
    )
    expect(screen.getByText('https://api.test').tagName).toBe('CODE')
    expect(container.querySelector('hr')).not.toBeNull()
  })

  it('"Forzar recarga" avisa sin navegar', async () => {
    const onRecargar = vi.fn()
    render(<PiePagina cargadoEn={new Date()} url="u" onRecargar={onRecargar} />)
    await userEvent.setup().click(screen.getByRole('link', { name: 'Forzar recarga' }))
    expect(onRecargar).toHaveBeenCalledTimes(1)
  })
})

describe('App: pie de página', () => {
  beforeEach(() => {
    window.location.hash = ''
  })

  it('aparece con los datos cargados y "Forzar recarga" vuelve a pedirlos a la API', async () => {
    const json = (c: unknown) => Promise.resolve(new Response(JSON.stringify(c), { status: 200 }))
    const fetchFn = vi.fn((url: string | URL | Request) =>
      json(String(url).includes('/historico') ? historicoApi() : listingsApi()),
    ) as unknown as typeof fetch
    render(<App opciones={{ apiUrl: 'http://api.test', fetchFn }} hoy="2026-07-21" />)
    const enlace = await screen.findByRole('link', { name: 'Forzar recarga' })
    expect(screen.getByText('http://api.test')).toBeInTheDocument()
    expect(document.querySelector('.pie')!.textContent).toMatch(/^Última actualización: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} · /)
    const antes = vi.mocked(fetchFn).mock.calls.length
    await userEvent.setup().click(enlace)
    await waitFor(() => expect(vi.mocked(fetchFn).mock.calls.length).toBe(antes * 2))
    expect(await screen.findByRole('link', { name: 'Forzar recarga' })).toBeInTheDocument()
  })
})
