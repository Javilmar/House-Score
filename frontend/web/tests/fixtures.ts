import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import type { ListingApi, PasadaDiariaApi } from '../src/types'

const leer = <T>(nombre: string): T =>
  JSON.parse(readFileSync(resolve(process.cwd(), 'tests/fixtures', nombre), 'utf8')) as T

export const listingsApi = (): ListingApi[] => leer('listings.json')
export const historicoApi = (): PasadaDiariaApi[] => leer('historico.json')
