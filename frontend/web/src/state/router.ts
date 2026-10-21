/**
 * Router por hash (contracts/vistas.md): `#/<vista>?<parámetros>`.
 * Ruta desconocida o vacía → `#/listados`. Un parámetro repetido se lee como array; un solo
 * valor como texto (quien consume normaliza con `comoLista`).
 */
import { useEffect, useMemo, useSyncExternalStore } from 'react'

export const VISTAS = [
  'listados',
  'top',
  'novedades',
  'evolucion',
  'bajadas',
  'hipoteca',
  'como-funciona',
  'mapas',
] as const

export type Vista = (typeof VISTAS)[number]
export type ParamsRuta = Record<string, string | string[]>
export type ParamsEntrada = Record<string, string | string[] | number | undefined | null>

export interface Ruta {
  vista: Vista
  params: ParamsRuta
}

const esVista = (s: string): s is Vista => (VISTAS as readonly string[]).includes(s)

function dividirHash(hash: string): { ruta: string; consulta: string } {
  const sinAlmohadilla = hash.startsWith('#') ? hash.slice(1) : hash
  const i = sinAlmohadilla.indexOf('?')
  const ruta = i === -1 ? sinAlmohadilla : sinAlmohadilla.slice(0, i)
  return { ruta: ruta.replace(/^\/+/, ''), consulta: i === -1 ? '' : sinAlmohadilla.slice(i + 1) }
}

export function parsearHash(hash: string): Ruta {
  const { ruta, consulta } = dividirHash(hash)
  if (!esVista(ruta)) return { vista: 'listados', params: {} }
  const params: ParamsRuta = {}
  for (const [clave, valor] of new URLSearchParams(consulta)) {
    const previo = params[clave]
    if (previo === undefined) params[clave] = valor
    else params[clave] = Array.isArray(previo) ? [...previo, valor] : [previo, valor]
  }
  return { vista: ruta, params }
}

export function formatearHash(vista: Vista, params: ParamsEntrada = {}): string {
  const qs = new URLSearchParams()
  for (const [clave, valor] of Object.entries(params)) {
    if (valor === undefined || valor === null) continue
    for (const v of Array.isArray(valor) ? valor : [valor]) {
      const texto = String(v)
      if (texto !== '') qs.append(clave, texto)
    }
  }
  const consulta = qs.toString()
  return consulta ? `#/${vista}?${consulta}` : `#/${vista}`
}

/** Normaliza un parámetro (texto o array) a lista. */
export const comoLista = (v: string | string[] | undefined): string[] =>
  v === undefined ? [] : Array.isArray(v) ? v : [v]

const oyentes = new Set<() => void>()
const avisar = () => oyentes.forEach((o) => o())

function suscribir(oyente: () => void): () => void {
  oyentes.add(oyente)
  window.addEventListener('hashchange', oyente)
  return () => {
    oyentes.delete(oyente)
    window.removeEventListener('hashchange', oyente)
  }
}

const leerHash = () => window.location.hash

export function navegar(vista: Vista, params?: ParamsEntrada): void {
  const hash = formatearHash(vista, params)
  if (window.location.hash !== hash) window.location.hash = hash
  avisar()
}

/** Reemplaza los parámetros de la vista actual sin añadir entrada de historial. */
export function setParams(params: ParamsEntrada): void {
  const { vista } = parsearHash(leerHash())
  const hash = formatearHash(vista, params)
  window.history.replaceState(window.history.state, '', hash)
  avisar()
}

export function useRuta(): {
  vista: Vista
  params: ParamsRuta
  navegar: typeof navegar
  setParams: typeof setParams
} {
  const hash = useSyncExternalStore(suscribir, leerHash, () => '')
  const { vista, params } = useMemo(() => parsearHash(hash), [hash])

  // Ruta desconocida o vacía → #/listados (sin añadir historial)
  useEffect(() => {
    if (!esVista(dividirHash(hash).ruta)) {
      window.history.replaceState(window.history.state, '', '#/listados')
      avisar()
    }
  }, [hash])

  return { vista, params, navegar, setParams }
}
