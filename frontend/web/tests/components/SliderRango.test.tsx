import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import SliderRango from '../../src/components/SliderRango'
import type { Rango } from '../../src/domain/filtros'

function montar(valor: Rango, props: Partial<React.ComponentProps<typeof SliderRango>> = {}) {
  const onChange = vi.fn()
  render(<SliderRango etiqueta="Precio" min={0} max={100} valor={valor} onChange={onChange} {...props} />)
  return {
    onChange,
    min: screen.getByRole('slider', { name: 'Precio (mínimo)' }),
    max: screen.getByRole('slider', { name: 'Precio (máximo)' }),
  }
}

/** Da un ancho conocido a la pista (jsdom no hace layout). */
function pista(): HTMLElement {
  const el = document.querySelector<HTMLElement>('.st-slider-pista')!
  el.getBoundingClientRect = () => ({ left: 100, width: 200, top: 0, right: 300, bottom: 4, height: 4, x: 100, y: 0, toJSON() {} })
  return el
}

describe('SliderRango', () => {
  it('tiene dos tiradores con rango, valor y texto accesibles', () => {
    const { min, max } = montar([20, 60], { formato: (n) => `${n} €` })
    expect(min).toHaveAttribute('aria-valuemin', '0')
    expect(min).toHaveAttribute('aria-valuemax', '100')
    expect(min).toHaveAttribute('aria-valuenow', '20')
    expect(min).toHaveAttribute('aria-valuetext', '20 €')
    expect(max).toHaveAttribute('aria-valuenow', '60')
    expect(max).toHaveAttribute('aria-valuetext', '60 €')
  })

  it('muestra el valor actual sobre cada tirador y los extremos del recorrido', () => {
    montar([20, 60], { formato: (n) => `${n} €` })
    expect([...document.querySelectorAll('.st-slider-valor')].map((e) => e.textContent)).toEqual(['20 €', '60 €'])
    expect([...document.querySelectorAll('.st-slider-extremos span')].map((e) => e.textContent)).toEqual(['0 €', '100 €'])
  })

  it('las flechas mueven solo el tirador enfocado y emiten [mín, máx]', async () => {
    const user = userEvent.setup()
    const { min, max, onChange } = montar([20, 60])
    min.focus()
    await user.keyboard('{ArrowRight}')
    expect(onChange).toHaveBeenLastCalledWith([21, 60])
    await user.keyboard('{ArrowLeft}{ArrowLeft}')
    expect(onChange).toHaveBeenLastCalledWith([19, 60])
    max.focus()
    await user.keyboard('{ArrowUp}')
    expect(onChange).toHaveBeenLastCalledWith([20, 61])
    await user.keyboard('{ArrowDown}')
    expect(onChange).toHaveBeenLastCalledWith([20, 59])
  })

  it('Inicio, Fin y RePág/AvPág saltan; respetan el paso y los extremos', async () => {
    const user = userEvent.setup()
    const { min, max, onChange } = montar([20, 60])
    min.focus()
    await user.keyboard('{Home}')
    expect(onChange).toHaveBeenLastCalledWith([0, 60])
    await user.keyboard('{PageUp}')
    expect(onChange).toHaveBeenLastCalledWith([30, 60])
    max.focus()
    await user.keyboard('{End}')
    expect(onChange).toHaveBeenLastCalledWith([20, 100])
    await user.keyboard('{PageDown}')
    expect(onChange).toHaveBeenLastCalledWith([20, 50])
  })

  it('los tiradores no se cruzan', async () => {
    const user = userEvent.setup()
    const { min, max, onChange } = montar([40, 40])
    min.focus()
    await user.keyboard('{ArrowRight}{End}')
    max.focus()
    await user.keyboard('{ArrowLeft}{Home}')
    expect(onChange).not.toHaveBeenCalled()
  })

  it('un tirador llega como mucho hasta el otro', async () => {
    const user = userEvent.setup()
    const { min, max, onChange } = montar([30, 50])
    min.focus()
    await user.keyboard('{End}')
    expect(onChange).toHaveBeenLastCalledWith([50, 50])
    max.focus()
    await user.keyboard('{Home}')
    expect(onChange).toHaveBeenLastCalledWith([30, 30])
  })

  it('el máximo se alcanza aunque no caiga en la rejilla del paso', async () => {
    const user = userEvent.setup()
    const { max, onChange } = montar([0, 2000], { max: 2500, step: 1000 })
    max.focus()
    await user.keyboard('{ArrowRight}')
    expect(onChange).toHaveBeenLastCalledWith([0, 2500])
  })

  it('pulsar la pista mueve el tirador más cercano al valor pulsado', () => {
    const { onChange } = montar([20, 60])
    const p = pista()
    fireEvent.pointerDown(p, { clientX: 260, pointerId: 1 }) // 80 %
    expect(onChange).toHaveBeenLastCalledWith([20, 80])
    fireEvent.pointerDown(p, { clientX: 100, pointerId: 1 }) // 0 %
    expect(onChange).toHaveBeenLastCalledWith([0, 60])
  })

  it('arrastrar acota el tirador al otro', () => {
    const { onChange } = montar([20, 60])
    const p = pista()
    fireEvent.pointerDown(p, { clientX: 140, pointerId: 1 }) // 20 % → tirador mínimo
    fireEvent.pointerMove(p, { clientX: 280, pointerId: 1 }) // 90 %: no puede pasar de 60
    expect(onChange).toHaveBeenLastCalledWith([60, 60])
    fireEvent.pointerUp(p, { pointerId: 1 })
    onChange.mockClear()
    fireEvent.pointerMove(p, { clientX: 180, pointerId: 1 })
    expect(onChange).not.toHaveBeenCalled()
  })

  it('sin recorrido (mín = máx) queda desactivado', async () => {
    const user = userEvent.setup()
    const { min, onChange } = montar([5, 5], { min: 5, max: 5 })
    expect(min).toHaveAttribute('aria-disabled', 'true')
    min.focus()
    await user.keyboard('{ArrowRight}')
    expect(onChange).not.toHaveBeenCalled()
  })
})
