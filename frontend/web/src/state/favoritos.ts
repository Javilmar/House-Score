/**
 * Favoritos: solo en este navegador (localStorage), sin backend ni datos personales.
 * Un único valor, `housescore:favoritos` = array JSON de urls de listing. Ausente, corrupto
 * o con el almacenamiento bloqueado → lista vacía (con bloqueo, los cambios viven en memoria).
 * Se sincroniza entre pestañas con el evento `storage`.
 */
import { useCallback, useSyncExternalStore } from 'react'

export const CLAVE_FAVORITOS = 'housescore:favoritos'

const VACIO: readonly string[] = Object.freeze([])
const oyentes = new Set<() => void>()
const avisar = () => oyentes.forEach((o) => o())

/** Se activa si el almacenamiento falla al escribir: desde entonces manda la memoria. */
let enMemoria: readonly string[] | null = null
let cache: { crudo: string | null; lista: readonly string[] } = { crudo: null, lista: VACIO }

function parsear(crudo: string | null): readonly string[] {
  if (crudo === null) return VACIO
  try {
    const v: unknown = JSON.parse(crudo)
    if (!Array.isArray(v)) return VACIO
    const urls = [...new Set(v.filter((x): x is string => typeof x === 'string' && x !== ''))]
    return urls.length ? urls : VACIO
  } catch {
    return VACIO
  }
}

/** Snapshot estable: la misma referencia mientras el texto guardado no cambie. */
function leer(): readonly string[] {
  if (enMemoria) return enMemoria
  let crudo: string | null
  try {
    crudo = window.localStorage.getItem(CLAVE_FAVORITOS)
  } catch {
    return VACIO
  }
  if (crudo !== cache.crudo) cache = { crudo, lista: parsear(crudo) }
  return cache.lista
}

function escribir(lista: readonly string[]): void {
  try {
    window.localStorage.setItem(CLAVE_FAVORITOS, JSON.stringify(lista))
    enMemoria = null
  } catch {
    enMemoria = lista.length ? lista : VACIO
  }
  avisar()
}

function suscribir(oyente: () => void): () => void {
  oyentes.add(oyente)
  const alCambiar = (e: StorageEvent) => {
    if (e.key === null || e.key === CLAVE_FAVORITOS) oyente()
  }
  window.addEventListener('storage', alCambiar)
  return () => {
    oyentes.delete(oyente)
    window.removeEventListener('storage', alCambiar)
  }
}

export function useFavoritos(): {
  favoritos: readonly string[]
  esFavorito: (url: string) => boolean
  alternar: (url: string) => void
  quitar: (url: string) => void
} {
  const favoritos = useSyncExternalStore(suscribir, leer, () => VACIO)
  const esFavorito = useCallback((url: string) => favoritos.includes(url), [favoritos])
  const alternar = useCallback((url: string) => {
    const actual = leer()
    escribir(actual.includes(url) ? actual.filter((u) => u !== url) : [...actual, url])
  }, [])
  const quitar = useCallback((url: string) => escribir(leer().filter((u) => u !== url)), [])
  return { favoritos, esFavorito, alternar, quitar }
}
