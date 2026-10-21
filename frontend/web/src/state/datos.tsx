import { createContext, useContext, useMemo, type ReactNode } from 'react'
import type { Listing, PasadaDiaria } from '../types'

export interface Datos {
  listings: Listing[]
  historico: PasadaDiaria[]
  /** Fecha local ISO yyyy-mm-dd; inyectable para los tests. */
  hoy: string
}

const DatosContext = createContext<Datos | null>(null)

/** Fecha local de hoy como `yyyy-mm-dd` (equivale a `date.today()` de app.py). */
export function hoyIso(ahora: Date = new Date()): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${ahora.getFullYear()}-${p(ahora.getMonth() + 1)}-${p(ahora.getDate())}`
}

interface Props {
  listings: Listing[]
  historico: PasadaDiaria[]
  hoy?: string
  children: ReactNode
}

/** Solo se monta en el estado `listo`: los datos ya están cargados y mapeados. */
export function DatosProvider({ listings, historico, hoy, children }: Props) {
  const fecha = hoy ?? hoyIso()
  const valor = useMemo(() => ({ listings, historico, hoy: fecha }), [listings, historico, fecha])
  return <DatosContext.Provider value={valor}>{children}</DatosContext.Provider>
}

export function useDatos(): Datos {
  const d = useContext(DatosContext)
  if (!d) throw new Error('useDatos debe usarse dentro de <DatosProvider> (solo en el estado listo)')
  return d
}
