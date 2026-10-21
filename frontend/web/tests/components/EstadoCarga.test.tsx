import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import EstadoCarga from '../../src/components/EstadoCarga'

const URL_API = 'https://api.test/listings?incluir_retirados=true'

describe('<EstadoCarga>', () => {
  it('cargando', () => {
    render(<EstadoCarga estado={{ fase: 'cargando' }} reintentar={() => {}} />)
    expect(screen.getByRole('status')).toHaveTextContent('Cargando…')
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('despertando: "Despertando el servidor…"', () => {
    render(<EstadoCarga estado={{ fase: 'despertando' }} reintentar={() => {}} />)
    expect(screen.getByText('Despertando el servidor…')).toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('sin datos: "Sin datos todavía", distinto de un error, con Reintentar', () => {
    render(<EstadoCarga estado={{ fase: 'sin_datos' }} reintentar={() => {}} />)
    expect(screen.getByText(/Sin datos todavía/)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
  })

  it.each([
    ['no_disponible', 'La API no ha respondido a tiempo', 'API no disponible'],
    ['limite', 'La API ha limitado las peticiones; espera un momento y pulsa Reintentar', 'Demasiadas peticiones'],
    ['http', 'La API ha devuelto un error (HTTP 503)', 'Error del servidor'],
    ['ilegible', 'La respuesta de la API no es válida', 'Respuesta ilegible'],
  ] as const)('error %s: título, detalle, URL consultada y Reintentar', async (tipo, detalle, titulo) => {
    const reintentar = vi.fn()
    render(<EstadoCarga estado={{ fase: 'error', tipo, url: URL_API, detalle }} reintentar={reintentar} />)
    const alerta = screen.getByRole('alert')
    expect(alerta).toHaveTextContent(titulo)
    expect(alerta).toHaveTextContent(detalle)
    expect(within(alerta).getByText(URL_API).tagName).toBe('CODE')
    await userEvent.setup().click(within(alerta).getByRole('button', { name: 'Reintentar' }))
    expect(reintentar).toHaveBeenCalledTimes(1)
  })

  it('en error no hay cifras ni datos', () => {
    const { container } = render(
      <EstadoCarga estado={{ fase: 'error', tipo: 'http', url: URL_API, detalle: 'La API ha devuelto un error (HTTP 503)' }} reintentar={() => {}} />,
    )
    expect(container.querySelector('.kpi-grid')).toBeNull()
    expect(container.textContent).not.toMatch(/Total listings|Precio medio/)
  })

  it('error sin URL conocida: no muestra la línea de dirección', () => {
    render(<EstadoCarga estado={{ fase: 'error', tipo: 'ilegible', url: '', detalle: 'La respuesta de la API no es válida' }} reintentar={() => {}} />)
    expect(screen.queryByText(/Dirección consultada/)).toBeNull()
  })
})
