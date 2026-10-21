import { act, fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { DatosProvider } from '../../src/state/datos'
import type { Listing } from '../../src/types'
import Bajadas from '../../src/views/Bajadas'
import Novedades from '../../src/views/Novedades'
import Top from '../../src/views/Top'
import { listing } from '../helpers'

const HOY = '2026-07-21'

function montar(vista: React.ReactElement, listings: Listing[]) {
  return render(
    <DatosProvider listings={listings} historico={[]} hoy={HOY}>
      {vista}
    </DatosProvider>,
  )
}

const tarjetas = () => [...document.querySelectorAll<HTMLElement>('.prop-card')]
const titulos = () => tarjetas().map((t) => t.querySelector('.prop-title')!.textContent)

beforeEach(() => {
  window.history.replaceState(null, '', '/')
})

describe('Top scoring', () => {
  const muchos = Array.from({ length: 32 }, (_, i) =>
    listing({ url: `https://x/${i}`, title: `Piso ${i}`, score: 100 - i, price: 100000 + i }),
  )
  const scrollIntoView = vi.fn()

  beforeEach(() => {
    window.history.replaceState(null, '', '/#/top')
    scrollIntoView.mockClear()
    Element.prototype.scrollIntoView = scrollIntoView
  })
  afterEach(() => vi.useRealTimers())

  it('encabezado, slider 5–30 con 15 por defecto y 15 tarjetas numeradas', () => {
    montar(<Top />, muchos)
    expect(screen.getByRole('heading', { level: 2, name: 'Top scoring' })).toBeInTheDocument()
    const slider = screen.getByRole('slider', { name: 'Mostrar top' })
    expect(slider).toHaveAttribute('min', '5')
    expect(slider).toHaveAttribute('max', '30')
    expect(slider).toHaveValue('15')
    expect(tarjetas()).toHaveLength(15)
    expect(tarjetas()[0]).toHaveAttribute('id', 'card-0')
    expect(tarjetas()[14]).toHaveAttribute('id', 'card-14')
    expect(tarjetas()[2]!.querySelector('.prop-rank')!.textContent).toBe('3.')
  })

  it('mover el slider cambia el número de tarjetas y lo refleja en el hash', () => {
    montar(<Top />, muchos)
    fireEvent.change(screen.getByRole('slider', { name: 'Mostrar top' }), { target: { value: '30' } })
    expect(tarjetas()).toHaveLength(30)
    expect(window.location.hash).toBe('#/top?n=30')
    fireEvent.change(screen.getByRole('slider', { name: 'Mostrar top' }), { target: { value: '5' } })
    expect(tarjetas()).toHaveLength(5)
  })

  it('el parámetro n del hash fija el slider', () => {
    window.history.replaceState(null, '', '/#/top?n=7')
    montar(<Top />, muchos)
    expect(screen.getByRole('slider', { name: 'Mostrar top' })).toHaveValue('7')
    expect(tarjetas()).toHaveLength(7)
  })

  it('contenido de la tarjeta: badge, título enlazado, meta, precios, chips, desglose y descripción', () => {
    const l = listing({
      url: 'https://x/a',
      title: '🏠 Piso Alfa',
      score: 71.5,
      price: 1234567,
      eur_m2: 2500,
      m2: 80,
      rooms: 3,
      bathrooms: 2,
      location: 'Getafe',
      floor: '3',
      year_built: 1999,
      energy_rating: 'D',
      score_details: ['🏊 Piscina (+10)', '⚠️ Sin ascensor (-5)'],
      description: 'Descripción larga del piso <b>no html</b>',
    })
    montar(<Top />, [l])
    const t = tarjetas()[0]!
    expect(t.querySelector('.score-badge')!.textContent).toBe('72')
    const enlace = within(t).getByRole('link', { name: 'Piso Alfa' })
    expect(enlace).toHaveAttribute('href', 'https://x/a')
    expect(enlace).toHaveAttribute('target', '_blank')
    const meta = [...t.querySelectorAll('.prop-meta .meta-item')].map((m) => m.textContent)
    expect(meta).toEqual(['Getafe', 'Planta 3', '1999', 'D'])
    expect(t.querySelector('.prop-price')!.textContent).toContain('1,234,567 €')
    expect(t.querySelector('.prop-price')!.textContent).toContain('2,500 €/m²')
    expect(t.querySelector('.prop-price')!.textContent).toContain('80 m²')
    expect(t.querySelector('.score-bar-fill')).toHaveStyle({ width: '71.5%' })
    expect([...t.querySelectorAll('.chip:not(.chip-warn)')].map((c) => c.textContent)).toEqual(['Piscina (+10)'])
    expect([...t.querySelectorAll('.chip-warn')].map((c) => c.textContent)).toEqual(['Sin ascensor (-5)'])
    expect(within(t).getByText('Ver desglose de puntuación')).toBeInTheDocument()
    const desc = within(t).getByText('Descripción')
    expect(desc.tagName).toBe('SUMMARY')
    expect(within(t).getByText('Descripción larga del piso <b>no html</b>')).toBeInTheDocument()
    expect(t.querySelector('.prop-title b')).toBeNull()
  })

  it('sin url http el título no es enlace y no hay descripción si es corta', () => {
    montar(<Top />, [listing({ url: 'ftp://x', title: 'Sin enlace', description: 'corta' })])
    const t = tarjetas()[0]!
    expect(within(t).queryByRole('link')).toBeNull()
    expect(t.querySelector('span.prop-title')!.textContent).toBe('Sin enlace')
    expect(within(t).queryByText('Descripción')).toBeNull()
  })

  it('€ Hipoteca abre Hipoteca con precio, tipo y CCAA precargados', async () => {
    const user = userEvent.setup()
    montar(<Top />, [
      listing({ title: 'Obra nueva en Illescas', price: 180000, location: 'Illescas', description: 'Promoción de obra nueva' }),
    ])
    await user.click(screen.getByRole('button', { name: '€ Hipoteca' }))
    expect(window.location.hash).toBe('#/hipoteca?precio=180000&tipo=obra-nueva&ccaa=clm')
  })

  it('id dentro de los N mostrados: scroll a la tarjeta y resaltado temporal', () => {
    vi.useFakeTimers()
    window.history.replaceState(null, '', '/#/top?id=' + encodeURIComponent('https://x/3'))
    montar(<Top />, muchos)
    expect(scrollIntoView).toHaveBeenCalledTimes(1)
    expect(scrollIntoView.mock.instances[0]).toBe(document.getElementById('card-3'))
    expect(document.getElementById('card-3')).toHaveClass('prop-card-resaltada')
    act(() => vi.advanceTimersByTime(1800))
    expect(document.getElementById('card-3')).not.toHaveClass('prop-card-resaltada')
  })

  it('id fuera de los N mostrados: no hay scroll ni resaltado', () => {
    window.history.replaceState(null, '', '/#/top?id=' + encodeURIComponent('https://x/20'))
    montar(<Top />, muchos)
    expect(scrollIntoView).not.toHaveBeenCalled()
    expect(document.querySelector('.prop-card-resaltada')).toBeNull()
  })
})

describe('Bajadas de precio', () => {
  const a = listing({ url: 'https://x/a', title: 'Piso A', price: 180000, price_drop: 20000, previous_price: 200000, score: 40, first_seen: '2026-07-01', location: 'Getafe', source: 'pisos.com' })
  const b = listing({ url: 'https://x/b', title: 'Piso B', price: 90000, price_drop: 30000, previous_price: 120000, score: 60, first_seen: '2026-07-10', location: 'Illescas', source: 'idealista', description: 'obra nueva' })
  const sin = listing({ url: 'https://x/s', title: 'Sin bajada', price_drop: null })

  beforeEach(() => window.history.replaceState(null, '', '/#/bajadas'))

  it('encabezado, subtítulo y selector con las 5 opciones y "Mayor bajada (€)" por defecto', () => {
    montar(<Bajadas />, [a, b, sin])
    expect(screen.getByRole('heading', { level: 2, name: 'Bajadas de precio' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 3, name: 'Listings con bajada de precio detectada' })).toBeInTheDocument()
    const sel = screen.getByRole('combobox', { name: 'Ordenar por' })
    expect([...sel.querySelectorAll('option')].map((o) => o.textContent)).toEqual([
      'Mayor bajada (€)',
      'Mayor bajada (%)',
      'Mejor score',
      'Precio más bajo',
      'Más reciente',
    ])
    expect(sel).toHaveValue('Mayor bajada (€)')
    expect(titulos()).toEqual(['Piso B', 'Piso A'])
  })

  it('cambiar el orden reordena y se refleja en el hash', async () => {
    const user = userEvent.setup()
    montar(<Bajadas />, [a, b])
    await user.selectOptions(screen.getByRole('combobox', { name: 'Ordenar por' }), 'Mejor score')
    expect(titulos()).toEqual(['Piso B', 'Piso A'])
    await user.selectOptions(screen.getByRole('combobox', { name: 'Ordenar por' }), 'Precio más bajo')
    expect(titulos()).toEqual(['Piso B', 'Piso A'])
    await user.selectOptions(screen.getByRole('combobox', { name: 'Ordenar por' }), 'Más reciente')
    expect(window.location.hash).toBe('#/bajadas?orden=M%C3%A1s+reciente')
    expect(titulos()).toEqual(['Piso B', 'Piso A'])
  })

  it('el parámetro orden del hash selecciona la opción', () => {
    window.history.replaceState(null, '', '/#/bajadas?orden=' + encodeURIComponent('Precio más bajo'))
    montar(<Bajadas />, [a, b])
    expect(screen.getByRole('combobox', { name: 'Ordenar por' })).toHaveValue('Precio más bajo')
  })

  it('tarjeta: precio anterior tachado, actual, % de bajada, días y meta', () => {
    montar(<Bajadas />, [a])
    const t = tarjetas()[0]!
    expect(t.querySelector('.score-badge')!.textContent).toBe('40')
    expect(t.querySelector('.prop-meta')!.textContent).toBe('Getafe · pisos.com · 20d en mercado')
    const previo = t.querySelector('.lc-precio-previo')!
    expect(previo.textContent).toBe('200,000 €')
    expect(previo).toHaveStyle({ textDecoration: 'line-through' })
    expect(t.textContent).toContain('180,000 €')
    expect(t.querySelector('.lc-badge-bajada')!.textContent).toBe('−10%')
  })

  it('€ Hipoteca usa el precio actual y abre Hipoteca', async () => {
    const user = userEvent.setup()
    montar(<Bajadas />, [b])
    await user.click(screen.getByRole('button', { name: '€ Hipoteca' }))
    expect(window.location.hash).toBe('#/hipoteca?precio=90000&tipo=obra-nueva&ccaa=clm')
  })

  it('sin bajadas: mensaje y sin selector', () => {
    montar(<Bajadas />, [sin])
    expect(
      screen.getByText('No se han detectado bajadas de precio todavía. Aparecerán aquí cuando un listing baje entre pasadas.'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('combobox')).toBeNull()
  })
})

describe('Novedades', () => {
  const n1 = listing({ url: 'https://x/1', title: 'Nuevo 1', first_seen: '2026-07-20', score: 50, price: 250000, m2: 80, eur_m2: 3125, rooms: 3, location: 'Getafe', source: 'idealista' })
  const n2 = listing({ url: 'https://x/2', title: 'Nuevo 2', first_seen: '2026-07-20', score: 80, price: 120000, m2: 60, eur_m2: 2000, rooms: 2, location: 'Illescas', source: 'pisos.com', description: 'Promoción de obra nueva' })
  const viejo = listing({ url: 'https://x/3', title: 'Viejo', first_seen: '2026-07-10' })

  beforeEach(() => window.history.replaceState(null, '', '/#/novedades'))

  it('encabezado, selector de pasada (más reciente primero) y contador', () => {
    montar(<Novedades />, [viejo, n1, n2])
    expect(screen.getByRole('heading', { level: 2, name: 'Novedades' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 3, name: 'Pisos nuevos por pasada' })).toBeInTheDocument()
    const pasada = screen.getByRole('combobox', { name: 'Pasada' })
    expect([...pasada.querySelectorAll('option')].map((o) => o.textContent)).toEqual(['2026-07-20', '2026-07-10'])
    expect(pasada).toHaveValue('2026-07-20')
    expect(document.querySelector('.lc-contador')!.textContent).toBe('2pisos nuevos en esta pasada')
    expect(titulos()).toEqual(['Nuevo 2', 'Nuevo 1'])
  })

  it('selector de orden con 4 opciones; "Precio más bajo" reordena', async () => {
    const user = userEvent.setup()
    montar(<Novedades />, [n1, n2])
    const orden = screen.getByRole('combobox', { name: 'Ordenar por' })
    expect([...orden.querySelectorAll('option')].map((o) => o.textContent)).toEqual([
      'Mejor score',
      'Precio más bajo',
      'Mayor superficie',
      'Más antiguo',
    ])
    await user.selectOptions(orden, 'Mayor superficie')
    expect(titulos()).toEqual(['Nuevo 1', 'Nuevo 2'])
    await user.selectOptions(orden, 'Precio más bajo')
    expect(titulos()).toEqual(['Nuevo 2', 'Nuevo 1'])
  })

  it('cambiar de pasada muestra solo los pisos de esa fecha', async () => {
    const user = userEvent.setup()
    montar(<Novedades />, [viejo, n1, n2])
    await user.selectOptions(screen.getByRole('combobox', { name: 'Pasada' }), '2026-07-10')
    expect(titulos()).toEqual(['Viejo'])
    expect(document.querySelector('.lc-contador')!.textContent).toBe('1pisos nuevos en esta pasada')
  })

  it('tarjeta: meta, detalles y precio con punto de miles', () => {
    montar(<Novedades />, [n1])
    const t = tarjetas()[0]!
    const metas = [...t.querySelectorAll('.prop-meta')].map((m) => m.textContent)
    expect(metas).toEqual(['Getafe · idealista', '80 m² · 3.125 €/m² · 3 hab'])
    expect(t.querySelector('.score-badge')!.textContent).toBe('50')
    expect(t.textContent).toContain('250.000 €')
  })

  it('€ Hipoteca abre Hipoteca con los datos de la tarjeta', async () => {
    const user = userEvent.setup()
    montar(<Novedades />, [n2])
    await user.click(screen.getByRole('button', { name: '€ Hipoteca' }))
    expect(window.location.hash).toBe('#/hipoteca?precio=120000&tipo=obra-nueva&ccaa=clm')
  })

  it('sin fechas de primera aparición: aviso de ejecuciones', () => {
    montar(<Novedades />, [listing({ first_seen: null })])
    expect(screen.getByText('No hay datos de ejecuciones disponibles.')).toBeInTheDocument()
    expect(screen.queryByRole('combobox')).toBeNull()
  })
})
