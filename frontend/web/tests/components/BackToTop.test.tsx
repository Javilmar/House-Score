import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import BackToTop from '../../src/components/BackToTop'

function scrollA(y: number) {
  Object.defineProperty(window, 'scrollY', { value: y, configurable: true })
  act(() => {
    fireEvent.scroll(window)
  })
}

describe('BackToTop', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'scrollY', { value: 0, configurable: true })
    window.scrollTo = vi.fn()
  })
  afterEach(() => vi.restoreAllMocks())

  it('está oculto hasta superar los 300 px de scroll', () => {
    render(<BackToTop />)
    expect(screen.queryByRole('button', { name: 'Volver arriba' })).toBeNull()
    scrollA(300)
    expect(screen.queryByRole('button', { name: 'Volver arriba' })).toBeNull()
    scrollA(301)
    expect(screen.getByRole('button', { name: 'Volver arriba' })).toHaveTextContent('↑')
    scrollA(10)
    expect(screen.queryByRole('button', { name: 'Volver arriba' })).toBeNull()
  })

  it('se muestra de inicio si la página ya está desplazada', () => {
    Object.defineProperty(window, 'scrollY', { value: 900, configurable: true })
    render(<BackToTop />)
    expect(screen.getByRole('button', { name: 'Volver arriba' })).toBeInTheDocument()
  })

  it('al pulsarlo sube al inicio con scroll suave', () => {
    render(<BackToTop />)
    scrollA(1000)
    fireEvent.click(screen.getByRole('button', { name: 'Volver arriba' }))
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' })
  })

  it('deja de escuchar el scroll al desmontarse', () => {
    const quitar = vi.spyOn(window, 'removeEventListener')
    const { unmount } = render(<BackToTop />)
    unmount()
    expect(quitar).toHaveBeenCalledWith('scroll', expect.any(Function))
  })
})
