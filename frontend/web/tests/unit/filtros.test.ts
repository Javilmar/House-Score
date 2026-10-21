import { describe, expect, it } from 'vitest'
import { mapearListings } from '../../src/api/mapeo'
import {
  aplicarFiltros,
  enriquecer,
  ordenar,
  paramsDeFiltros,
  resolverFiltros,
  type Columna,
} from '../../src/domain/filtros'
import type { ParamsRuta } from '../../src/state/router'
import { listingsApi } from '../fixtures'
import { listing } from '../helpers'

const HOY = '2026-07-21'

const MUESTRA = enriquecer([
  listing({ url: 'u1', title: 'A', municipio: 'getafe', location: 'Getafe', score: 90, price: 100000, rooms: 1 }),
  listing({ url: 'u2', title: 'B', municipio: 'parla', location: 'Parla', score: 70, price: 150000, rooms: 2 }),
  listing({ url: 'u3', title: 'C', municipio: 'illescas', location: 'Illescas', score: 50, price: 200000, rooms: 3 }),
  listing({ url: 'u4', title: 'D', municipio: 'sesena', location: 'Seseña', score: 30, price: 250000, rooms: 4 }),
  listing({ url: 'u5', title: 'E', municipio: '', location: 'Madrid (Vallecas)', score: 10, price: 90000, rooms: 2, status: 'delisted' }),
])

const urls = (filas: { l: { url: string } }[]) => filas.map((f) => f.l.url)

describe('enriquecer', () => {
  it('deriva zona, municipio, tipo y ranking global (posición en el orden de entrada)', () => {
    expect(MUESTRA.map((f) => f.zona)).toEqual(['Madrid Sur', 'Madrid Sur', 'Toledo Norte', 'Toledo Norte', '—'])
    expect(MUESTRA.map((f) => f.municipio)).toEqual(['Getafe', 'Parla', 'Illescas', 'Sesena', 'Vallecas'])
    expect(MUESTRA.map((f) => f.rank)).toEqual([0, 1, 2, 3, 4])
    expect(MUESTRA.every((f) => f.tipo === 'Segunda mano')).toBe(true)
  })
})

describe('resolverFiltros: valores por defecto', () => {
  it('sin parámetros: oculta retirados, rangos completos, nada seleccionado', () => {
    const { base, filtros, opciones } = resolverFiltros(MUESTRA, {})
    expect(urls(base)).toEqual(['u1', 'u2', 'u3', 'u4'])
    expect(filtros).toEqual({
      retirados: false,
      zonas: [],
      municipios: [],
      score: [0, 100],
      precio: [100000, 250000],
      hab: [1, 4],
    })
    expect(opciones.zonas).toEqual(['Madrid Sur', 'Toledo Norte'])
    expect(opciones.municipios).toEqual(['Getafe', 'Illescas', 'Parla', 'Sesena'])
    expect(urls(aplicarFiltros(base, filtros))).toEqual(['u1', 'u2', 'u3', 'u4'])
  })

  it('"Mostrar retirados" amplía la base, las zonas disponibles y los límites del precio', () => {
    const { base, filtros, opciones } = resolverFiltros(MUESTRA, { retirados: '1' })
    expect(urls(base)).toHaveLength(5)
    expect(filtros.retirados).toBe(true)
    expect(filtros.precio).toEqual([90000, 250000])
    expect(opciones.zonas).toEqual(['Madrid Sur', 'Toledo Norte'])
    expect(opciones.municipios).toContain('Vallecas')
  })

  it('sliders sin recorrido (min == max) no filtran: precio/hab null', () => {
    const una = enriquecer([listing({ price: 5, rooms: 2 }), listing({ price: 5, rooms: 2 })])
    const { filtros } = resolverFiltros(una, {})
    expect(filtros.hab).toBeNull()
    expect(filtros.precio).toEqual([5, 5])
  })

  it('"—" no es una opción de zona ni de municipio', () => {
    const f = enriquecer([listing({ municipio: '', location: 'sin nada' })])
    const { opciones } = resolverFiltros(f, {})
    expect(opciones.zonas).toEqual([])
    expect(opciones.municipios).toEqual([])
  })
})

describe('filtros combinativos (app.py:1267-1291)', () => {
  it('la zona acota las opciones de municipio', () => {
    const { opciones } = resolverFiltros(MUESTRA, { zona: 'Toledo Norte' })
    expect(opciones.municipios).toEqual(['Illescas', 'Sesena'])
    const dos = resolverFiltros(MUESTRA, { zona: ['Madrid Sur', 'Toledo Norte'] })
    expect(dos.opciones.municipios).toHaveLength(4)
  })

  it('una selección de municipio fuera de la zona elegida se descarta', () => {
    const { filtros, opciones } = resolverFiltros(MUESTRA, { zona: 'Toledo Norte', muni: ['Getafe', 'Illescas'] })
    expect(opciones.municipios).toEqual(['Illescas', 'Sesena'])
    expect(filtros.municipios).toEqual(['Illescas'])
  })

  it('zona + municipio + score + precio + habitaciones se combinan con AND inclusivo', () => {
    const { base, filtros } = resolverFiltros(MUESTRA, {
      zona: 'Madrid Sur',
      score: '70-100',
      precio: '100000-150000',
      hab: '2-4',
    })
    expect(filtros.score).toEqual([70, 100])
    expect(urls(aplicarFiltros(base, filtros))).toEqual(['u2'])
    const solo = resolverFiltros(MUESTRA, { muni: 'Parla' })
    expect(urls(aplicarFiltros(solo.base, solo.filtros))).toEqual(['u2'])
  })

  it('límites inclusivos en score', () => {
    const { base, filtros } = resolverFiltros(MUESTRA, { score: '50-70' })
    expect(urls(aplicarFiltros(base, filtros))).toEqual(['u2', 'u3'])
  })

  it('el resultado sale por score descendente y los retirados solo si se piden', () => {
    const r = resolverFiltros(MUESTRA, { retirados: '1' })
    expect(urls(aplicarFiltros(r.base, r.filtros))).toEqual(['u1', 'u2', 'u3', 'u4', 'u5'])
  })

  it('valores fuera de rango se acotan; basura vuelve al valor por defecto', () => {
    const r = resolverFiltros(MUESTRA, { score: '-5-500', precio: '1-999999999', hab: 'xx', zona: 'Marte' })
    expect(r.filtros.score).toEqual([0, 100])
    expect(r.filtros.precio).toEqual([100000, 250000])
    expect(r.filtros.hab).toEqual([1, 4])
    expect(r.filtros.zonas).toEqual([])
  })
})

describe('paramsDeFiltros (hash)', () => {
  it('los valores por defecto no aparecen; lo demás sí y vuelve a leerse igual', () => {
    const { filtros, opciones } = resolverFiltros(MUESTRA, {})
    expect(paramsDeFiltros(filtros, opciones)).toEqual({})
    const cambiado = {
      ...filtros,
      retirados: true,
      zonas: ['Madrid Sur'],
      municipios: ['Parla'],
      score: [10, 80] as [number, number],
      precio: [100000, 200000] as [number, number],
      hab: [2, 4] as [number, number],
    }
    const base = resolverFiltros(MUESTRA, { retirados: '1' })
    const p = paramsDeFiltros(cambiado, base.opciones)
    expect(p).toEqual({
      retirados: '1',
      zona: ['Madrid Sur'],
      muni: ['Parla'],
      score: '10-80',
      precio: '100000-200000',
      hab: '2-4',
    })
    expect(resolverFiltros(MUESTRA, p as ParamsRuta).filtros).toEqual(cambiado)
  })
})

describe('ordenar (JS ord(), app.py:522)', () => {
  const orden = (col: Columna, dir: 'asc' | 'desc', filas = MUESTRA) => urls(ordenar(filas, col, dir, HOY))

  it('numéricos ascendente y descendente', () => {
    expect(orden('precio', 'asc')).toEqual(['u5', 'u1', 'u2', 'u3', 'u4'])
    expect(orden('precio', 'desc')).toEqual(['u4', 'u3', 'u2', 'u1', 'u5'])
    expect(orden('score', 'asc')).toEqual(['u5', 'u4', 'u3', 'u2', 'u1'])
  })

  it('texto sin distinguir mayúsculas ni acentos (localeCompare es, base)', () => {
    const f = enriquecer([
      listing({ url: 'a', title: 'Árbol' }),
      listing({ url: 'b', title: 'abeja' }),
      listing({ url: 'c', title: 'Zeta' }),
    ])
    expect(orden('titulo', 'asc', f)).toEqual(['b', 'a', 'c'])
    expect(orden('titulo', 'desc', f)).toEqual(['c', 'a', 'b'])
  })

  it('los números van antes que los vacíos en ascendente (y al revés en descendente)', () => {
    const f = enriquecer([
      listing({ url: 'a', eur_m2: null }),
      listing({ url: 'b', eur_m2: 3000 }),
      listing({ url: 'c', eur_m2: 1000 }),
    ])
    expect(orden('eur_m2', 'asc', f)).toEqual(['c', 'b', 'a'])
    expect(orden('eur_m2', 'desc', f)).toEqual(['a', 'b', 'c'])
  })

  it('días: sin fecha cuenta como 9999; ordena por antigüedad', () => {
    const f = enriquecer([
      listing({ url: 'a', first_seen: null }),
      listing({ url: 'b', first_seen: '2026-07-20' }),
      listing({ url: 'c', first_seen: '2026-06-01' }),
    ])
    expect(orden('dias', 'asc', f)).toEqual(['b', 'c', 'a'])
  })

  it('es estable y no muta la entrada', () => {
    const f = enriquecer([listing({ url: 'a', price: 1 }), listing({ url: 'b', price: 1 }), listing({ url: 'c', price: 0 })])
    const antes = urls(f)
    expect(orden('precio', 'asc', f)).toEqual(['c', 'a', 'b'])
    expect(urls(f)).toEqual(antes)
  })

  it('tipo, fuente y ubicación ordenan por texto', () => {
    expect(orden('ubicacion', 'asc')).toEqual(['u5', 'u1', 'u2', 'u3', 'u4'])
    expect(orden('fuente', 'asc')).toHaveLength(5)
    expect(orden('tipo', 'asc')).toHaveLength(5)
  })
})

describe('rendimiento (SC-006): filtrar y ordenar el fixture completo', () => {
  const todos = mapearListings(listingsApi())

  it('el fixture tiene más de 2.000 listings', () => {
    expect(todos.length).toBeGreaterThanOrEqual(2000)
  })

  it('enriquecer + filtrar + ordenar < 200 ms', () => {
    const t0 = performance.now()
    const filas = enriquecer(todos)
    const { base, filtros } = resolverFiltros(filas, { retirados: '1', score: '10-95', hab: '1-4' })
    const filtradas = aplicarFiltros(base, filtros)
    for (const col of ['titulo', 'precio', 'score', 'eur_m2', 'tipo', 'ubicacion', 'dias'] as Columna[])
      ordenar(filtradas, col, 'desc', HOY)
    const ms = performance.now() - t0
    expect(filtradas.length).toBeGreaterThan(0)
    expect(ms).toBeLessThan(200)
  })
})
