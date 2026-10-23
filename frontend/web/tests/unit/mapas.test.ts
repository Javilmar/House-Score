import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  CENTRO,
  COLOR_CRIMINALIDAD,
  COLOR_PRECIO,
  COLOR_RENTA,
  agregarPrecios,
  capasDisponibles,
  capaActiva,
  figuraCriminalidad,
  figuraPrecio,
  figuraRenta,
  leerCriminalidad,
  leerSecciones,
  notaCriminalidad,
  notaPrecio,
  notaRenta,
  rankingCriminalidad,
  rankingPrecio,
  rankingRenta,
  slugMunicipio,
  sinDatoCriminalidad,
  type GeoJson,
} from '../../src/domain/mapas'
import { mapearListings } from '../../src/api/mapeo'
import { listingsApi } from '../fixtures'

const listings = mapearListings(listingsApi())
const asset = (n: string) => readFileSync(resolve(process.cwd(), 'public/assets', n), 'utf8')
const geoMun = JSON.parse(asset('municipios_zona.geojson')) as GeoJson
const geoSec = JSON.parse(asset('secciones_renta.geojson')) as GeoJson
const crim = leerCriminalidad(asset('criminalidad.csv'))
const renta = leerSecciones(geoSec)

describe('carga de assets', () => {
  it('criminalidad.csv: ignora comentarios #, campos entrecomillados y cod_ine como texto', () => {
    expect(crim).toHaveLength(12)
    expect(crim[0]).toEqual({
      cod_ine: '28007',
      municipio: 'Alcorcón',
      tasa_criminalidad: 3295.6,
      periodo: 'Q1 2026 (ene-mar), anualizado',
    })
    expect(crim.at(-1)?.cod_ine).toBe('45161')
  })

  it('secciones: una fila por feature, renta numérica', () => {
    expect(renta).toHaveLength(1539)
    expect(renta[0]!.cusec).toMatch(/^\d{10}$/)
    expect(typeof renta[0]!.renta_persona).toBe('number')
  })

  it('capas disponibles en orden: criminalidad, renta, precio', () => {
    expect(capasDisponibles(true, true).map((c) => c.id)).toEqual(['criminalidad', 'renta', 'precio'])
    expect(capasDisponibles(false, true).map((c) => c.id)).toEqual(['renta', 'precio'])
    expect(capasDisponibles(false, false).map((c) => c.id)).toEqual(['precio'])
    expect(capasDisponibles(true, true).map((c) => c.etiqueta)).toEqual([
      '🔴  Criminalidad · por municipio',
      '🟢  Renta · por barrio (sección censal)',
      '🟡  Precio vivienda · por municipio',
    ])
  })

  it('capaActiva: parámetro válido o la primera disponible', () => {
    const c = capasDisponibles(true, true)
    expect(capaActiva(c, undefined)).toBe('criminalidad')
    expect(capaActiva(c, 'renta')).toBe('renta')
    expect(capaActiva(c, 'precio')).toBe('precio')
    expect(capaActiva(c, 'xx')).toBe('criminalidad')
    expect(capaActiva(capasDisponibles(false, true), 'criminalidad')).toBe('renta')
  })
})

describe('figura de criminalidad', () => {
  const { data, layout } = figuraCriminalidad(crim, geoMun)
  const t = data[0] as Record<string, any>

  it('traza choroplethmap con join por properties.cod_ine (texto)', () => {
    expect(t.type).toBe('choroplethmap')
    expect(t.featureidkey).toBe('properties.cod_ine')
    expect(t.locations).toEqual(crim.map((r) => r.cod_ine))
    expect(t.locations.every((l: unknown) => typeof l === 'string')).toBe(true)
    expect(t.z).toEqual(crim.map((r) => r.tasa_criminalidad))
    expect(t.geojson).toBe(geoMun)
    const ids = new Set(geoMun.features.map((f) => String(f.properties.cod_ine)))
    expect(t.locations.every((l: string) => ids.has(l))).toBe(true)
  })

  it('escala, rango, opacidad, hover y colorbar', () => {
    const tasas = crim.map((r) => r.tasa_criminalidad)
    expect(t.colorscale).toEqual(COLOR_CRIMINALIDAD)
    expect(COLOR_CRIMINALIDAD).toEqual([
      [0.0, '#22c55e'],
      [0.35, '#84cc16'],
      [0.55, '#eab308'],
      [0.75, '#f97316'],
      [1.0, '#ef4444'],
    ])
    expect(t.zmin).toBeCloseTo(Math.min(...tasas) * 0.85)
    expect(t.zmax).toBeCloseTo(Math.max(...tasas) * 1.05)
    expect(t.marker.opacity).toBe(0.75)
    expect(t.hovertext).toEqual(crim.map((r) => r.municipio))
    expect(t.hovertemplate).toBe(
      '<b>%{hovertext}</b><br>Tasa / 100 000 hab=%{z:.0f}<br>Período=%{customdata[0]}<extra></extra>',
    )
    expect(t.customdata[0]).toEqual(['Q1 2026 (ene-mar), anualizado'])
    expect(t.colorbar).toMatchObject({
      orientation: 'h',
      x: 0.5,
      xanchor: 'center',
      y: -0.04,
      yanchor: 'top',
      thickness: 10,
      len: 0.72,
      title: { text: 'Tasa / 100 000 hab', side: 'top', font: { color: '#a1a1aa', size: 11 } },
      tickfont: { color: '#a1a1aa', size: 10 },
      bgcolor: 'rgba(0,0,0,0)',
      bordercolor: '#27272a',
    })
  })

  it('layout: mapa oscuro, centro, zoom 9 y márgenes de _MAP_LAYOUT', () => {
    expect(CENTRO).toEqual({ lat: 40.36, lon: -3.66 })
    expect(layout.map).toEqual({ style: 'carto-darkmatter', center: CENTRO, zoom: 9 })
    expect(layout.height).toBe(540)
    expect(layout.margin).toEqual({ l: 0, r: 0, t: 0, b: 48 })
    expect(layout.paper_bgcolor).toBe('rgba(0,0,0,0)')
    expect(layout.plot_bgcolor).toBe('rgba(0,0,0,0)')
    expect(layout.font).toEqual({ family: 'Inter', size: 12, color: '#a1a1aa' })
    expect(layout.hoverlabel).toEqual({
      bgcolor: '#18181b',
      bordercolor: '#27272a',
      font: { family: 'Inter', color: '#e4e4e7' },
    })
  })
})

describe('municipios sin dato (grises)', () => {
  it('son los del geojson cuyo cod_ine no está en el CSV, ordenados por nombre', () => {
    const sin = sinDatoCriminalidad(crim, geoMun)
    expect(sin).toHaveLength(64 - 12)
    expect(sin).toEqual([...sin].sort())
    expect(sin).not.toContain('Alcorcón')
  })

  it('el join normaliza cod_ine numérico a texto', () => {
    const geo: GeoJson = {
      type: 'FeatureCollection',
      features: [
        { type: 'Feature', properties: { cod_ine: '28007', nombre: 'A' }, geometry: null },
        { type: 'Feature', properties: { cod_ine: '28999', nombre: 'B' }, geometry: null },
      ],
    }
    const filas = leerCriminalidad('cod_ine,municipio,tasa_criminalidad,periodo\n28007,A,10,P')
    expect(sinDatoCriminalidad(filas, geo)).toEqual(['B'])
  })
})

describe('figura de renta', () => {
  const { data, layout } = figuraRenta(renta, geoSec)
  const t = data[0] as Record<string, any>
  it('join por properties.cusec, escala y rango', () => {
    const v = renta.map((r) => r.renta_persona as number)
    expect(t.featureidkey).toBe('properties.cusec')
    expect(t.locations).toEqual(renta.map((r) => r.cusec))
    expect(t.colorscale).toEqual(COLOR_RENTA)
    expect(COLOR_RENTA[0]).toEqual([0.0, '#ef4444'])
    expect(COLOR_RENTA[4]).toEqual([1.0, '#22c55e'])
    expect(t.zmin).toBeCloseTo(Math.min(...v) * 0.9)
    expect(t.zmax).toBeCloseTo(Math.max(...v) * 1.05)
    expect(t.hovertemplate).toBe(
      '<b>%{hovertext}</b><br>Sección censal=%{location}<br>Renta neta media (€/pers)=%{z:,.0f}<br>Año=%{customdata[0]}<extra></extra>',
    )
    expect(t.colorbar.title.text).toBe('Renta neta media (€/pers)')
    expect(layout.map).toEqual({ style: 'carto-darkmatter', center: CENTRO, zoom: 9 })
  })

  it('las secciones sin renta no se pintan', () => {
    const f = [...renta.slice(0, 2), { ...renta[2]!, renta_persona: null }]
    const t2 = figuraRenta(f, geoSec).data[0] as Record<string, any>
    expect(t2.locations).toHaveLength(2)
  })
})

describe('precio por municipio', () => {
  it('slugMunicipio equivale a _slug_muni', () => {
    expect(slugMunicipio('Torrejón de la Calzada')).toBe('torrejon_de_la_calzada')
    expect(slugMunicipio('Cubas de la Sagra')).toBe('cubas_de_la_sagra')
    expect(slugMunicipio("L'Hospitalet-Sur")).toBe('lhospitalet_sur')
  })

  const filas = agregarPrecios(listings, geoMun)

  it('agrega mediana de €/m², mediana de precio y nº de anuncios con cod_ine del geojson', () => {
    expect(filas.length).toBeGreaterThan(0)
    const f = filas.find((r) => r.nombre === 'Fuenlabrada')!
    const mias = listings.filter((l) => l.municipio === 'fuenlabrada' && l.eur_m2 != null)
    expect(f.n_listings).toBe(mias.length)
    const med = (xs: number[]) => {
      const s = [...xs].sort((a, b) => a - b)
      const m = s.length >> 1
      return s.length % 2 ? s[m]! : (s[m - 1]! + s[m]!) / 2
    }
    expect(f.eur_m2_med).toBeCloseTo(med(mias.map((l) => l.eur_m2 as number)))
    expect(f.precio_med).toBeCloseTo(med(mias.map((l) => l.price)))
    expect(f.cod_ine).toMatch(/^28/)
  })

  it('municipios sin geojson o sin eur_m2 se descartan', () => {
    const rows = agregarPrecios(
      [
        { ...listings[0]!, municipio: 'no_existe', eur_m2: 3000 },
        { ...listings[0]!, municipio: 'fuenlabrada', eur_m2: null },
      ],
      geoMun,
    )
    expect(rows).toEqual([])
  })

  it('figura: escala, rango 0.9/1.05, zoom 9, hover', () => {
    const { data, layout } = figuraPrecio(filas, geoMun)
    const t = data[0] as Record<string, any>
    const v = filas.map((r) => r.eur_m2_med)
    expect(t.colorscale).toEqual(COLOR_PRECIO)
    expect(t.featureidkey).toBe('properties.cod_ine')
    expect(t.zmin).toBeCloseTo(Math.min(...v) * 0.9)
    expect(t.zmax).toBeCloseTo(Math.max(...v) * 1.05)
    expect(t.colorbar.title.text).toBe('€/m² mediana')
    expect(t.hovertemplate).toBe(
      '<b>%{hovertext}</b><br>€/m² (mediana)=%{z:,.0f}<br>Precio mediano (€)=%{customdata[0]:,.0f}<br>Anuncios=%{customdata[1]}<extra></extra>',
    )
    expect(layout.map).toMatchObject({ zoom: 9 })
  })

  it('ranking de precio ascendente con formato de miles inglés', () => {
    const r = rankingPrecio(filas)
    const orden = [...filas].sort((a, b) => a.eur_m2_med - b.eur_m2_med)
    expect(r.map((x) => x.Municipio)).toEqual(orden.map((x) => x.nombre))
    expect(r[0]!['€/m² mediana']).toBe(Math.round(orden[0]!.eur_m2_med).toLocaleString('en-US'))
    expect(r[0]!.Anuncios).toBe(orden[0]!.n_listings)
  })
})

describe('rankings', () => {
  it('criminalidad: descendente, sin decimales', () => {
    const r = rankingCriminalidad(crim)
    expect(r[0]).toEqual({ Municipio: 'Valdemoro', 'Tasa / 100 000 hab': '7885' })
    const tasas = [...crim].sort((a, b) => b.tasa_criminalidad - a.tasa_criminalidad)
    expect(r.map((x) => x.Municipio)).toEqual(tasas.map((x) => x.municipio))
    expect(r).toHaveLength(12)
  })

  it('renta: descendente, todas las secciones, miles con coma', () => {
    const r = rankingRenta(renta)
    expect(r).toHaveLength(1539)
    const max = Math.max(...renta.map((x) => x.renta_persona as number))
    expect(r[0]!['Renta neta media (€/pers)']).toBe(Math.round(max).toLocaleString('en-US'))
    expect(Object.keys(r[0]!)).toEqual(['Municipio', 'Sección censal', 'Renta neta media (€/pers)'])
  })
})

describe('notas (texto literal)', () => {
  it('criminalidad', () => {
    expect(notaCriminalidad('Q1 2026 (ene-mar), anualizado')).toBe(
      '**Fuente**: Portal Estadístico de Criminalidad · Ministerio del Interior · **Período**: Q1 2026 (ene-mar), anualizado · **Métrica**: infracciones penales / 100 000 hab · **Rojo** = más peligroso · **Verde** = más seguro · **Gris** = sin publicación oficial (<20 000 hab)',
    )
  })
  it('renta', () => {
    expect(notaRenta('2023', 0)).toBe(
      '**Fuente**: Atlas de Distribución de Renta de los Hogares (ADRH 2023) · INE · **Métrica**: renta neta media por persona (€/año) · **Verde** = renta alta · **Rojo** = renta baja · **Gris** = sin publicación oficial (0 secciones) · ⚠️ Renta ≠ criminalidad — proxy socioeconómico del barrio',
    )
  })
  it('precio', () => {
    expect(notaPrecio(7)).toBe(
      '**Fuente**: anuncios scrapeados (pisos.com + fotocasa) · **Métrica**: mediana de €/m² por municipio · **Verde** = más barato · **Rojo** = más caro · **Gris** = sin anuncios (7 municipios)',
    )
  })
})
