import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Icon, { ICON_NAMES } from '../../src/components/Icon'

describe('Icon', () => {
  it('expone los iconos Lucide de app.py:68-82 más info (pestaña Cómo funciona)', () => {
    expect([...ICON_NAMES].sort()).toEqual(
      [
        'layers', 'sparkles', 'star', 'wallet', 'trending-down', 'waves', 'map-pin',
        'building', 'calendar', 'zap', 'ruler', 'bed', 'bath', 'info',
      ].sort(),
    )
  })

  it('renderiza el svg con los atributos por defecto de icon() (size 16, currentColor, stroke 1.75)', () => {
    const { container } = render(<Icon name="star" />)
    const svg = container.querySelector('svg')!
    expect(svg).toHaveAttribute('width', '16')
    expect(svg).toHaveAttribute('height', '16')
    expect(svg).toHaveAttribute('viewBox', '0 0 24 24')
    expect(svg).toHaveAttribute('fill', 'none')
    expect(svg).toHaveAttribute('stroke', 'currentColor')
    expect(svg).toHaveAttribute('stroke-width', '1.75')
    expect(svg).toHaveAttribute('stroke-linecap', 'round')
    expect(svg).toHaveAttribute('stroke-linejoin', 'round')
    expect(svg.style.verticalAlign).toBe('-2px')
    expect(svg.style.flexShrink).toBe('0')
    expect(svg.querySelectorAll('path')).toHaveLength(1)
  })

  it('acepta size, color y stroke', () => {
    const { container } = render(<Icon name="wallet" size={18} color="#818cf8" stroke={2} />)
    const svg = container.querySelector('svg')!
    expect(svg).toHaveAttribute('width', '18')
    expect(svg).toHaveAttribute('stroke', '#818cf8')
    expect(svg).toHaveAttribute('stroke-width', '2')
    expect(svg.querySelectorAll('path')).toHaveLength(2)
  })

  it('número de elementos por icono igual al de app.py', () => {
    const esperado: Record<string, number> = {
      layers: 3, sparkles: 1, star: 1, wallet: 2, 'trending-down': 2, waves: 3,
      'map-pin': 2, building: 7, calendar: 4, zap: 1, ruler: 5, bed: 4, bath: 6, info: 3,
    }
    for (const [name, n] of Object.entries(esperado)) {
      const { container } = render(<Icon name={name} />)
      expect(container.querySelector('svg')!.children, name).toHaveLength(n)
    }
  })

  it('map-pin incluye circle cx12 cy10 r3 y calendar un rect 18x18', () => {
    const pin = render(<Icon name="map-pin" />).container.querySelector('circle')!
    expect([pin.getAttribute('cx'), pin.getAttribute('cy'), pin.getAttribute('r')]).toEqual(['12', '10', '3'])
    const rect = render(<Icon name="calendar" />).container.querySelector('rect')!
    expect([rect.getAttribute('width'), rect.getAttribute('height'), rect.getAttribute('rx')]).toEqual(['18', '18', '2'])
  })

  it('nombre desconocido → svg vacío', () => {
    const { container } = render(<Icon name="no-existe" />)
    const svg = container.querySelector('svg')!
    expect(svg).toBeInTheDocument()
    expect(svg.children).toHaveLength(0)
  })
})
