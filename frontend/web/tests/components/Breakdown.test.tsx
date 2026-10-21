import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import Breakdown from '../../src/components/Breakdown'
import ScoreBadge from '../../src/components/ScoreBadge'
import { listing } from '../helpers'

const l = listing({ score: 30, score_details: ['💰 Precio/m² bajo (+20)', '⚠️ Sin ascensor (-5)', '🏊 (+15)'] })

describe('<Breakdown>', () => {
  it('summary, filas con signo y clase, y total', () => {
    const { container } = render(<Breakdown listing={l} />)
    expect(screen.getByText('Ver desglose de puntuación').tagName).toBe('SUMMARY')
    const filas = container.querySelectorAll('tr.sb-row')
    expect(filas).toHaveLength(3)
    expect(filas[0]!.textContent).toBe('💰 Precio/m² bajo+20')
    expect(filas[0]!.querySelector('.sb-pts-pos')).not.toBeNull()
    expect(filas[1]!.querySelector('.sb-pts-neg')!.textContent).toBe('-5')
    expect(filas[2]!.textContent).toBe('🏊 Piscina+15')
    expect(container.querySelector('tr.sb-total')!.textContent).toBe('Total30')
  })
  it('puntos 0 → sb-pts-zero; el ajuste de reconciliación aparece', () => {
    const { container } = render(<Breakdown listing={listing({ score: 8, score_details: ['📅 Sin dato'] })} />)
    expect(container.querySelector('.sb-pts-zero')!.textContent).toBe('0')
    expect([...container.querySelectorAll('tr.sb-row')].at(-1)!.textContent).toBe('Ajuste (límite 0-100)+8')
  })
  it('sin ítems no renderiza nada', () => {
    const { container } = render(<Breakdown listing={listing({ score: 0, score_details: [] })} />)
    expect(container.firstChild).toBeNull()
  })
  it('diferido: las filas solo existen una vez abierto el desplegable', async () => {
    const { container } = render(<Breakdown listing={l} diferido />)
    expect(container.querySelectorAll('tr.sb-row')).toHaveLength(0)
    await userEvent.setup().click(screen.getByText('Ver desglose de puntuación'))
    expect(container.querySelectorAll('tr.sb-row')).toHaveLength(3)
  })
})

describe('<ScoreBadge>', () => {
  it('muestra el score redondeado sobre el color de la escala', () => {
    const { container } = render(<ScoreBadge score={63.4} />)
    const b = container.querySelector('.score-badge') as HTMLElement
    expect(b.textContent).toBe('63')
    expect(b.style.background).toBe('rgb(132, 204, 22)') // #84cc16
  })
})
