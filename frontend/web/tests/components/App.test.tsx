import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../../src/App'
import { historicoApi, listingsApi } from '../fixtures'

const ETIQUETAS = [
  'Listados completos',
  'Top scoring',
  'Novedades',
  'Evolución y análisis',
  'Bajadas de precio',
  'Hipoteca',
  'Cómo funciona',
  'Mapas',
  'Favoritos',
]

const json = (c: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(c), { status }))
const fetchOk = vi.fn((url: string | URL | Request) =>
  json(String(url).includes('/historico') ? historicoApi() : listingsApi()),
) as unknown as typeof fetch

beforeEach(() => {
  window.location.hash = ''
  window.history.replaceState(null, '', '/')
})

describe('App: armazón', () => {
  it('muestra cabecera y las 9 pestañas en el orden de app.py:1121, cada una con icono', async () => {
    render(<App opciones={{ apiUrl: 'http://api.test', fetchFn: fetchOk }} hoy="2026-07-21" />)
    expect(await screen.findByRole('heading', { level: 1, name: 'House Score' })).toBeInTheDocument()
    expect(
      screen.getByText('Madrid Sur, Este, Sureste y Norte · Toledo Norte — pisos.com · fotocasa · Scoring a medida · Hasta 300.000–400.000 € según zona'),
    ).toBeInTheDocument()
    const tabs = await screen.findAllByRole('tab')
    expect(tabs.map((t) => t.textContent)).toEqual(ETIQUETAS)
    for (const t of tabs) expect(t.querySelector('svg')).not.toBeNull()
  })

  it('la pestaña activa sigue al hash y por defecto es Listados completos', async () => {
    render(<App opciones={{ apiUrl: 'http://api.test', fetchFn: fetchOk }} hoy="2026-07-21" />)
    const activa = async () =>
      (await screen.findAllByRole('tab')).filter((t) => t.getAttribute('aria-selected') === 'true')
    expect((await activa()).map((t) => t.textContent)).toEqual(['Listados completos'])
    expect(window.location.hash).toBe('#/listados')
    expect(screen.getByRole('heading', { level: 2, name: 'Listados completos' })).toBeInTheDocument()
  })

  it('pulsar cada pestaña cambia el hash y renderiza su vista', async () => {
    const user = userEvent.setup()
    render(<App opciones={{ apiUrl: 'http://api.test', fetchFn: fetchOk }} hoy="2026-07-21" />)
    const rutas = ['listados', 'top', 'novedades', 'evolucion', 'bajadas', 'hipoteca', 'como-funciona', 'mapas', 'favoritos']
    const tabs = await screen.findAllByRole('tab')
    for (const [i, t] of tabs.entries()) {
      await user.click(t)
      expect(window.location.hash).toBe(`#/${rutas[i]}`)
      expect(t).toHaveAttribute('aria-selected', 'true')
      expect(screen.getByRole('heading', { level: 2, name: ETIQUETAS[i]! })).toBeInTheDocument()
    }
  })

  it('el hash inicial restaura la vista', async () => {
    window.location.hash = '#/hipoteca?precio=250000'
    render(<App opciones={{ apiUrl: 'http://api.test', fetchFn: fetchOk }} hoy="2026-07-21" />)
    expect(await screen.findByRole('heading', { level: 2, name: 'Hipoteca' })).toBeInTheDocument()
  })
})

describe('App: estados de carga', () => {
  it('error: aviso con la URL consultada, sin pestañas ni cifras, y Reintentar vuelve a pedir', async () => {
    const user = userEvent.setup()
    let fallar = true
    const f = vi.fn((url: string | URL | Request) =>
      fallar ? json({}, 503) : json(String(url).includes('/historico') ? historicoApi() : listingsApi()),
    ) as unknown as typeof fetch
    render(<App opciones={{ apiUrl: 'http://api.test', fetchFn: f }} hoy="2026-07-21" />)
    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('503')
    expect(alerta).toHaveTextContent('http://api.test/')
    expect(screen.queryAllByRole('tab')).toHaveLength(0)
    fallar = false
    await user.click(within(alerta).getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findAllByRole('tab')).toHaveLength(9)
  })

  it('sin_datos: "Sin datos todavía"', async () => {
    const f = vi.fn(() => json([])) as unknown as typeof fetch
    render(<App opciones={{ apiUrl: 'http://api.test', fetchFn: f }} hoy="2026-07-21" />)
    expect(await screen.findByText(/Sin datos todavía/)).toBeInTheDocument()
    expect(screen.queryAllByRole('tab')).toHaveLength(0)
  })

  it('despertando a los 3 s', async () => {
    vi.useFakeTimers()
    try {
      const f = vi.fn(() => new Promise<Response>(() => {})) as unknown as typeof fetch
      render(<App opciones={{ apiUrl: 'http://api.test', fetchFn: f }} hoy="2026-07-21" />)
      expect(screen.getByText(/Cargando/)).toBeInTheDocument()
      await act(() => vi.advanceTimersByTimeAsync(3_000))
      expect(screen.getByText('Despertando el servidor…')).toBeInTheDocument()
    } finally {
      vi.useRealTimers()
    }
  })
})
