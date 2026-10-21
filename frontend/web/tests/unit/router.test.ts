import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { formatearHash, parsearHash, useRuta, VISTAS } from '../../src/state/router'

describe('parsearHash / formatearHash', () => {
  it('las 8 vistas, en el orden de pestañas, se parsean y serializan', () => {
    expect(VISTAS).toEqual([
      'listados',
      'top',
      'novedades',
      'evolucion',
      'bajadas',
      'hipoteca',
      'como-funciona',
      'mapas',
    ])
    for (const v of VISTAS) {
      expect(parsearHash(`#/${v}`)).toEqual({ vista: v, params: {} })
      expect(formatearHash(v)).toBe(`#/${v}`)
    }
  })

  it('ruta desconocida, vacía o sin hash → listados', () => {
    for (const h of ['', '#', '#/', '#/nope', '#nope', '#/listados2', '#/?zona=a', '#/TOP/x']) {
      expect(parsearHash(h).vista).toBe('listados')
    }
  })

  it('ruta desconocida conserva params vacíos (no hereda los de otra vista)', () => {
    expect(parsearHash('#/nope?zona=a').params).toEqual({})
  })

  it('parámetros simples y repetidos (→ array)', () => {
    expect(parsearHash('#/listados?zona=Madrid%20Sur&muni=getafe&muni=leganes&score=40-80&retirados=1')).toEqual({
      vista: 'listados',
      params: { zona: 'Madrid Sur', muni: ['getafe', 'leganes'], score: '40-80', retirados: '1' },
    })
  })

  it('round-trip de params de cada vista del contrato', () => {
    const casos: [Parameters<typeof formatearHash>[0], Record<string, string | string[]>][] = [
      ['listados', { zona: 'Madrid Sur', muni: ['getafe', 'torrejon de la calzada'], score: '30-100', precio: '0-300000', hab: '2-4', retirados: '1' }],
      ['top', { n: '20', id: 'https://www.pisos.com/comprar/a/?x=1&y=2#z' }],
      ['bajadas', { orden: 'Mayor bajada (€)' }],
      ['hipoteca', { precio: '250000', tipo: 'obra-nueva', ccaa: 'clm' }],
      ['mapas', { capa: 'renta' }],
    ]
    for (const [vista, params] of casos) {
      const hash = formatearHash(vista, params)
      expect(parsearHash(hash)).toEqual({ vista, params })
    }
  })

  it('números se serializan como texto; vacíos/null/undefined/[] se omiten', () => {
    expect(formatearHash('top', { n: 15 })).toBe('#/top?n=15')
    expect(formatearHash('top', { n: '', id: [] })).toBe('#/top')
    expect(parsearHash(formatearHash('hipoteca', { precio: 250000 })).params).toEqual({ precio: '250000' })
  })

  it('un solo valor en array vuelve como texto (los consumidores normalizan)', () => {
    expect(parsearHash(formatearHash('listados', { muni: ['getafe'] })).params).toEqual({ muni: 'getafe' })
  })

  it('un parámetro sin valor se lee como cadena vacía', () => {
    expect(parsearHash('#/top?id=').params).toEqual({ id: '' })
  })
})

describe('useRuta', () => {
  beforeEach(() => {
    window.location.hash = ''
    window.history.replaceState(null, '', '/')
  })

  it('hash vacío → listados y el hash se normaliza a #/listados', () => {
    const { result } = renderHook(() => useRuta())
    expect(result.current.vista).toBe('listados')
    expect(window.location.hash).toBe('#/listados')
  })

  it('ruta desconocida → listados y se reescribe el hash', () => {
    window.location.hash = '#/zzz'
    const { result } = renderHook(() => useRuta())
    expect(result.current.vista).toBe('listados')
    expect(window.location.hash).toBe('#/listados')
  })

  it('lee la vista y los params iniciales del hash (recargar restaura)', () => {
    window.location.hash = '#/hipoteca?precio=250000&tipo=obra-nueva&ccaa=clm'
    const { result } = renderHook(() => useRuta())
    expect(result.current.vista).toBe('hipoteca')
    expect(result.current.params).toEqual({ precio: '250000', tipo: 'obra-nueva', ccaa: 'clm' })
  })

  it('navegar cambia vista y params, escribe el hash y añade entrada de historial', () => {
    const { result } = renderHook(() => useRuta())
    const antes = window.history.length
    act(() => result.current.navegar('top', { id: 'https://x/1', n: 20 }))
    expect(result.current.vista).toBe('top')
    expect(result.current.params).toEqual({ id: 'https://x/1', n: '20' })
    expect(window.location.hash).toBe('#/top?id=https%3A%2F%2Fx%2F1&n=20')
    expect(window.history.length).toBe(antes + 1)
  })

  it('navegar sin params limpia los de la vista anterior', () => {
    window.location.hash = '#/listados?zona=Madrid%20Sur'
    const { result } = renderHook(() => useRuta())
    act(() => result.current.navegar('mapas'))
    expect(result.current.params).toEqual({})
    expect(window.location.hash).toBe('#/mapas')
  })

  it('setParams reemplaza los params sin añadir historial', () => {
    window.location.hash = '#/listados'
    const { result } = renderHook(() => useRuta())
    const antes = window.history.length
    act(() => result.current.setParams({ zona: 'Toledo Norte', muni: ['illescas', 'yeles'] }))
    expect(result.current.vista).toBe('listados')
    expect(result.current.params).toEqual({ zona: 'Toledo Norte', muni: ['illescas', 'yeles'] })
    expect(window.location.hash).toBe('#/listados?zona=Toledo+Norte&muni=illescas&muni=yeles')
    expect(window.history.length).toBe(antes)
    act(() => result.current.setParams({}))
    expect(window.location.hash).toBe('#/listados')
  })

  it('reacciona a hashchange externo (botón atrás, enlace compartido)', () => {
    const { result } = renderHook(() => useRuta())
    act(() => {
      window.location.hash = '#/bajadas?orden=x'
      window.dispatchEvent(new HashChangeEvent('hashchange'))
    })
    expect(result.current.vista).toBe('bajadas')
    expect(result.current.params).toEqual({ orden: 'x' })
  })

  it('dos componentes que usan useRuta ven el mismo estado tras setParams', () => {
    const a = renderHook(() => useRuta())
    const b = renderHook(() => useRuta())
    act(() => a.result.current.setParams({ n: '10' }))
    expect(b.result.current.params).toEqual({ n: '10' })
  })
})
