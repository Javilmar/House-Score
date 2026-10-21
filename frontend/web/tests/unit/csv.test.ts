import { describe, expect, it } from 'vitest'
import { COLUMNAS_CSV, generarCsv, nombreCsv } from '../../src/domain/csv'
import { listing } from '../helpers'

describe('csv (app.py:1289-1308, 1470-1471)', () => {
  it('columnas en el orden de app.py', () => {
    expect(COLUMNAS_CSV).toEqual([
      'title', 'price', 'score', 'eur_m2', 'location', 'm2', 'rooms', 'bathrooms',
      'floor', 'year_built', 'energy_rating', 'source', 'first_seen', 'url',
    ])
  })
  it('nombre listings_<fecha>.csv', () => {
    expect(nombreCsv('2026-07-21')).toBe('listings_2026-07-21.csv')
  })
  it('cabecera + una línea por listing, null vacío', () => {
    const csv = generarCsv([
      listing({ title: 'A', price: 1000, score: 55, eur_m2: null, location: 'Getafe', m2: 0, first_seen: null, url: 'https://x/1' }),
    ])
    const [cab, fila, resto] = csv.split('\n')
    expect(cab).toBe('title,price,score,eur_m2,location,m2,rooms,bathrooms,floor,year_built,energy_rating,source,first_seen,url')
    expect(fila).toBe('A,1000,55,,Getafe,0,3,1,,0,,pisos.com,,https://x/1')
    expect(resto).toBe('')
  })
  it('entrecomilla comas, comillas y saltos de línea (QUOTE_MINIMAL)', () => {
    const csv = generarCsv([listing({ title: 'Piso, "luminoso"\nreformado', location: 'a,b' })])
    expect(csv).toContain('"Piso, ""luminoso""\nreformado"')
    expect(csv).toContain(',"a,b",')
  })
  it('sin filas: solo la cabecera', () => {
    expect(generarCsv([])).toBe(COLUMNAS_CSV.join(',') + '\n')
  })
})
