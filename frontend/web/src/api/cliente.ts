/**
 * Cliente de lectura de la API (contracts/api-lectura.md). Una sola petición GET por llamada,
 * sin reintentos; cualquier fallo se clasifica en un `ErrorApi` (equivalente a ApiNoDisponible).
 */
import type { ListingApi, PasadaDiariaApi } from '../types'

export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'
/** Tiempo máximo de espera de una petición (arranque en frío de la API ≈ 1 min). */
export const TIMEOUT_MS = 90_000

export type TipoError = 'no_disponible' | 'limite' | 'http' | 'ilegible'

export class ErrorApi extends Error {
  readonly tipo: TipoError
  readonly url: string
  readonly detalle: string

  constructor(tipo: TipoError, detalle: string, url: string) {
    super(`${detalle} (${url})`)
    this.name = 'ErrorApi'
    this.tipo = tipo
    this.url = url
    this.detalle = detalle
  }
}

export interface OpcionesPeticion {
  apiUrl?: string
  params?: Record<string, string>
  fetchFn?: typeof fetch
  timeoutMs?: number
  /** Cancelación externa (no genera error: la promesa se rechaza con la razón del aborto). */
  signal?: AbortSignal
}

export function urlApi(ruta: string, { apiUrl = API_URL, params }: OpcionesPeticion = {}): string {
  const base = `${apiUrl.replace(/\/+$/, '')}${ruta}`
  const qs = params ? new URLSearchParams(params).toString() : ''
  return qs ? `${base}?${qs}` : base
}

const esObjeto = (x: unknown): x is Record<string, unknown> =>
  typeof x === 'object' && x !== null && !Array.isArray(x)

export async function pedirLista(
  ruta: string,
  opciones: OpcionesPeticion = {},
): Promise<Record<string, unknown>[]> {
  const { fetchFn = fetch, timeoutMs = TIMEOUT_MS, signal } = opciones
  const url = urlApi(ruta, opciones)
  const controlador = new AbortController()
  let agotado = false
  const temporizador = setTimeout(() => {
    agotado = true
    controlador.abort()
  }, timeoutMs)
  const cancelar = () => controlador.abort(signal?.reason)
  if (signal?.aborted) cancelar()
  else signal?.addEventListener('abort', cancelar, { once: true })

  try {
    let respuesta: Response
    try {
      respuesta = await fetchFn(url, { method: 'GET', signal: controlador.signal })
    } catch (e) {
      if (signal?.aborted) throw e
      if (agotado) throw new ErrorApi('no_disponible', 'La API no ha respondido a tiempo', url)
      throw new ErrorApi('no_disponible', 'No se puede conectar con la API', url)
    }

    if (respuesta.status === 429) {
      throw new ErrorApi(
        'limite',
        'La API ha limitado las peticiones; espera un momento y pulsa Reintentar',
        url,
      )
    }
    if (respuesta.status !== 200) {
      throw new ErrorApi('http', `La API ha devuelto un error (HTTP ${respuesta.status})`, url)
    }

    let datos: unknown
    try {
      datos = await respuesta.json()
    } catch (e) {
      if (signal?.aborted) throw e
      if (agotado) throw new ErrorApi('no_disponible', 'La API no ha respondido a tiempo', url)
      throw new ErrorApi('ilegible', 'La respuesta de la API no es válida', url)
    }
    if (!Array.isArray(datos) || !datos.every(esObjeto)) {
      throw new ErrorApi('ilegible', 'La respuesta de la API no es válida', url)
    }
    return datos
  } finally {
    clearTimeout(temporizador)
    signal?.removeEventListener('abort', cancelar)
  }
}

export const obtenerListings = (opciones: OpcionesPeticion = {}) =>
  pedirLista('/listings', { ...opciones, params: { incluir_retirados: 'true' } }) as unknown as Promise<
    ListingApi[]
  >

export const obtenerHistorico = (opciones: OpcionesPeticion = {}) =>
  pedirLista('/historico', opciones) as unknown as Promise<PasadaDiariaApi[]>
