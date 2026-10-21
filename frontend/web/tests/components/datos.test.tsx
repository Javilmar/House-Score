import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { DatosProvider, useDatos } from '../../src/state/datos'
import type { Listing } from '../../src/types'

function Sonda() {
  const { listings, historico, hoy } = useDatos()
  return <p>{`${listings.length}|${historico.length}|${hoy}`}</p>
}

describe('DatosProvider / useDatos', () => {
  it('expone listings, historico y hoy inyectable', () => {
    render(
      <DatosProvider listings={[{} as Listing]} historico={[]} hoy="2026-07-21">
        <Sonda />
      </DatosProvider>,
    )
    expect(screen.getByText('1|0|2026-07-21')).toBeInTheDocument()
  })

  it('hoy por defecto es la fecha local ISO yyyy-mm-dd', () => {
    vi.useFakeTimers({ now: new Date(2026, 9, 21, 23, 30) })
    try {
      render(
        <DatosProvider listings={[]} historico={[]}>
          <Sonda />
        </DatosProvider>,
      )
      expect(screen.getByText('0|0|2026-10-21')).toBeInTheDocument()
    } finally {
      vi.useRealTimers()
    }
  })

  it('fuera del proveedor lanza error', () => {
    const err = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<Sonda />)).toThrow(/DatosProvider/)
    err.mockRestore()
  })
})
