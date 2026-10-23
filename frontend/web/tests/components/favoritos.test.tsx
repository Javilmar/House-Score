import { act, render, renderHook, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DatosProvider } from '../../src/state/datos'
import { CLAVE_FAVORITOS, useFavoritos } from '../../src/state/favoritos'
import type { Listing } from '../../src/types'
import Favoritos from '../../src/views/Favoritos'
import Listados from '../../src/views/Listados'
import Top from '../../src/views/Top'
import { listing } from '../helpers'

const A = listing({ url: 'https://x/a', title: 'Piso Alfa', score: 90 })
const B = listing({ url: 'https://x/b', title: 'Piso Beta', score: 80, status: 'delisted' })

function montar(vista: React.ReactElement, listings: Listing[] = [A, B]) {
  return render(
    <DatosProvider listings={listings} historico={[]} hoy="2026-07-21">
      {vista}
    </DatosProvider>,
  )
}

const guardado = () => JSON.parse(window.localStorage.getItem(CLAVE_FAVORITOS) ?? 'null')

beforeEach(() => {
  window.localStorage.clear()
  window.history.replaceState(null, '', '/')
})

describe('favoritos: estado', () => {
  it('alternar persiste en localStorage y sobrevive a un remontaje', () => {
    const { result, unmount } = renderHook(() => useFavoritos())
    act(() => result.current.alternar('https://x/a'))
    expect(guardado()).toEqual(['https://x/a'])
    expect(result.current.esFavorito('https://x/a')).toBe(true)
    unmount()
    const otra = renderHook(() => useFavoritos())
    expect(otra.result.current.favoritos).toEqual(['https://x/a'])
    act(() => otra.result.current.alternar('https://x/a'))
    expect(guardado()).toEqual([])
  })

  it('JSON corrupto o de otro tipo → lista vacía sin lanzar', () => {
    for (const crudo of ['{no es json', '{"a":1}', '"texto"', '[1,null,"https://x/a"]']) {
      window.localStorage.setItem(CLAVE_FAVORITOS, crudo)
      const { result, unmount } = renderHook(() => useFavoritos())
      expect(result.current.favoritos).toEqual(crudo.includes('https://x/a') ? ['https://x/a'] : [])
      unmount()
    }
  })

  it('almacenamiento bloqueado: no lanza y trabaja en memoria', () => {
    const get = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('bloqueado')
    })
    const set = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('bloqueado')
    })
    const { result } = renderHook(() => useFavoritos())
    expect(result.current.favoritos).toEqual([])
    act(() => result.current.alternar('https://x/a'))
    expect(result.current.favoritos).toEqual(['https://x/a'])
    get.mockRestore()
    set.mockRestore()
    act(() => result.current.alternar('https://x/a'))
    expect(result.current.favoritos).toEqual([])
  })

  it('el evento storage de otra pestaña actualiza la lista', () => {
    const { result } = renderHook(() => useFavoritos())
    window.localStorage.setItem(CLAVE_FAVORITOS, JSON.stringify(['https://x/b']))
    act(() => {
      window.dispatchEvent(new StorageEvent('storage', { key: CLAVE_FAVORITOS }))
    })
    expect(result.current.favoritos).toEqual(['https://x/b'])
  })
})

describe('favoritos: estrella', () => {
  it('en Top: botón con aria-pressed que guarda y se conserva al remontar', async () => {
    const user = userEvent.setup()
    const { unmount } = montar(<Top />)
    const estrella = screen.getByRole('button', { name: /Añadir a favoritos: Piso Alfa/ })
    expect(estrella).toHaveAttribute('aria-pressed', 'false')
    await user.click(estrella)
    expect(screen.getByRole('button', { name: /Quitar de favoritos: Piso Alfa/ })).toHaveAttribute('aria-pressed', 'true')
    expect(guardado()).toEqual(['https://x/a'])
    unmount()
    montar(<Top />)
    expect(screen.getByRole('button', { name: /Quitar de favoritos: Piso Alfa/ })).toHaveAttribute('aria-pressed', 'true')
  })

  it('en cada fila de Listados', async () => {
    const user = userEvent.setup()
    montar(<Listados />, [A])
    await user.click(screen.getByRole('button', { name: /Añadir a favoritos: Piso Alfa/ }))
    expect(guardado()).toEqual(['https://x/a'])
  })
})

describe('Favoritos (vista)', () => {
  it('sin favoritos explica que se guardan solo en este navegador', () => {
    montar(<Favoritos />)
    expect(screen.getByRole('heading', { level: 2, name: 'Favoritos' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('solo en este navegador')
  })

  it('lista los favoritos, marca el retirado y permite quitarlos', async () => {
    const user = userEvent.setup()
    window.localStorage.setItem(CLAVE_FAVORITOS, JSON.stringify(['https://x/a', 'https://x/b']))
    montar(<Favoritos />)
    const tarjetas = [...document.querySelectorAll<HTMLElement>('.prop-card')]
    expect(tarjetas).toHaveLength(2)
    expect(within(tarjetas[0]!).getByText('Piso Alfa')).toBeInTheDocument()
    expect(within(tarjetas[0]!).queryByText('retirado')).toBeNull()
    expect(within(tarjetas[1]!).getByText('Piso Beta')).toBeInTheDocument()
    expect(within(tarjetas[1]!).getByText('retirado')).toBeInTheDocument()
    await user.click(within(tarjetas[1]!).getByRole('button', { name: /Quitar de favoritos/ }))
    expect(guardado()).toEqual(['https://x/a'])
    expect(document.querySelectorAll('.prop-card')).toHaveLength(1)
  })

  it('un favorito que ya no está en los datos sale como fila mínima con su url y se puede quitar', async () => {
    const user = userEvent.setup()
    window.localStorage.setItem(CLAVE_FAVORITOS, JSON.stringify(['https://x/zzz']))
    montar(<Favoritos />)
    expect(screen.getByText('https://x/zzz')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Quitar de favoritos' }))
    expect(guardado()).toEqual([])
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
