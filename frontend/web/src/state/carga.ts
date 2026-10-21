/**
 * Máquina de estados de carga (data-model.md):
 *
 *   cargando ──(3 s sin respuesta)──▶ despertando ──(respuesta)──▶ listo | sin_datos
 *      └──────────(error o 90 s)───────────┴──▶ error{tipo, url} ──(reintentar)──▶ cargando
 *
 * Desde `error` no hay transiciones automáticas (FR-005): solo `reintentar()`.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ErrorApi,
  obtenerHistorico,
  obtenerListings,
  type OpcionesPeticion,
  type TipoError,
} from '../api/cliente'
import { mapearHistorico, mapearListings } from '../api/mapeo'
import type { Listing, PasadaDiaria } from '../types'

export const AVISO_DESPERTANDO_MS = 3_000

export type EstadoCarga =
  | { fase: 'cargando' }
  | { fase: 'despertando' }
  | { fase: 'listo'; listings: Listing[]; historico: PasadaDiaria[] }
  | { fase: 'sin_datos' }
  | { fase: 'error'; tipo: TipoError; url: string; detalle: string }

export interface OpcionesCarga extends Omit<OpcionesPeticion, 'signal' | 'params'> {
  avisoMs?: number
}

/** Inicia una carga; devuelve la función que la cancela (tras cancelar no se emite ningún estado). */
export function iniciarCarga(alCambiar: (estado: EstadoCarga) => void, opciones: OpcionesCarga = {}): () => void {
  const { avisoMs = AVISO_DESPERTANDO_MS, ...peticion } = opciones
  const controlador = new AbortController()
  let vigente = true
  const emitir = (e: EstadoCarga) => {
    if (vigente) alCambiar(e)
  }

  emitir({ fase: 'cargando' })
  const aviso = setTimeout(() => emitir({ fase: 'despertando' }), avisoMs)

  Promise.all([
    obtenerListings({ ...peticion, signal: controlador.signal }),
    obtenerHistorico({ ...peticion, signal: controlador.signal }),
  ])
    .then(([listings, historico]) => {
      clearTimeout(aviso)
      if (listings.length === 0) emitir({ fase: 'sin_datos' })
      else emitir({ fase: 'listo', listings: mapearListings(listings), historico: mapearHistorico(historico) })
    })
    .catch((e: unknown) => {
      clearTimeout(aviso)
      controlador.abort() // corta la otra petición
      if (e instanceof ErrorApi) emitir({ fase: 'error', tipo: e.tipo, url: e.url, detalle: e.detalle })
      else emitir({ fase: 'error', tipo: 'ilegible', url: '', detalle: 'La respuesta de la API no es válida' })
    })

  return () => {
    vigente = false
    clearTimeout(aviso)
    controlador.abort()
  }
}

export function useCarga(opciones?: OpcionesCarga): { estado: EstadoCarga; reintentar: () => void } {
  const [estado, setEstado] = useState<EstadoCarga>({ fase: 'cargando' })
  const [intento, setIntento] = useState(0)
  const opcionesRef = useRef(opciones)

  useEffect(() => iniciarCarga(setEstado, opcionesRef.current), [intento])
  const reintentar = useCallback(() => setIntento((n) => n + 1), [])
  return { estado, reintentar }
}
