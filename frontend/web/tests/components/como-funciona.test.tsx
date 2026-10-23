import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ComoFunciona from '../../src/views/ComoFunciona'

const bloque = (titulo: string) => screen.getByText(titulo).closest('.prop-card') as HTMLElement

describe('Cómo funciona', () => {
  it('introducción y nota final literales', () => {
    render(<ComoFunciona />)
    expect(screen.getByText(/puntuación de 0 a 100/)).toBeInTheDocument()
    expect(screen.getByText(/Así se reparten los puntos:/)).toBeInTheDocument()
    expect(
      screen.getByText('La puntuación es orientativa: ayuda a priorizar, no sustituye una visita.'),
    ).toBeInTheDocument()
  })

  it('los 7 bloques de scoring con sus filas y colores', () => {
    render(<ComoFunciona />)
    const titulos = [
      '💎 Valor vs zona',
      '📐 Superficie',
      '📈 Señales de mercado',
      '✨ Características',
      '🌿 Exterior',
      '➕ Extras (suman)',
      '⚠️ Penalizaciones (restan)',
    ]
    for (const t of titulos) expect(bloque(t)).toBeInTheDocument()

    const valor = bloque('💎 Valor vs zona')
    expect(within(valor).getByText('€/m² frente a la media de su municipio')).toBeInTheDocument()
    expect(within(valor).getByText('+25')).toHaveStyle({ color: '#22c55e' })
    expect(within(valor).getByText('≈ +12')).toHaveStyle({ color: '#818cf8' })
    expect(within(valor).getByText('+0')).toHaveStyle({ color: '#f87171' })
    expect(within(valor).getByText('fuera del Top')).toHaveStyle({ color: '#f87171' })
    expect(within(valor).getByText('Sin m² fiable → no se puede valorar')).toBeInTheDocument()

    const sup = bloque('📐 Superficie')
    for (const [c, p] of [['≥ 140 m²', '+15'], ['≥ 120 m²', '+12'], ['≥ 100 m²', '+8'], ['≥ 80 m²', '+5']] as const) {
      expect(within(sup).getByText(c)).toBeInTheDocument()
      expect(within(sup).getAllByText(p).length).toBeGreaterThan(0)
    }

    const mercado = bloque('📈 Señales de mercado')
    expect(within(mercado).getByText('📉 Ha bajado de precio')).toBeInTheDocument()
    expect(within(mercado).getByText('+1 a +5')).toBeInTheDocument()
    expect(within(mercado).getByText('🕸️ Lleva > 45 días anunciado')).toBeInTheDocument()
    expect(within(mercado).getByText('−3')).toBeInTheDocument()
    expect(within(mercado).getByText('−5')).toBeInTheDocument()

    const car = bloque('✨ Características')
    expect(within(car).getByText('Detectadas en anuncio y ficha · el total se limita a +18')).toBeInTheDocument()
    expect(within(car).getByText('🏊 Piscina')).toBeInTheDocument()
    expect(within(car).getByText('máx +18')).toHaveStyle({ color: '#818cf8' })
    expect(within(car).queryByText('🌿 Terraza / 🏡 Patio')).toBeNull()

    const ext = bloque('🌿 Exterior')
    expect(within(ext).getByText('Terraza, patio, jardín o balcón')).toBeInTheDocument()
    expect(within(ext).getByText('Ficha leída y sin exterior')).toBeInTheDocument()
    expect(within(ext).getByText('−25')).toHaveStyle({ color: '#f87171' })

    const extras = bloque('➕ Extras (suman)')
    expect(within(extras).getByText('⚡ Eficiencia energética A/B/C')).toBeInTheDocument()
    expect(within(extras).getByText('🏗️ Obra nueva / a estrenar')).toBeInTheDocument()

    const pen = bloque('⚠️ Penalizaciones (restan)')
    expect(within(pen).getByText('−3 a −20')).toBeInTheDocument()
    expect(within(pen).queryByText(/Ocupada/)).toBeNull()
    expect(within(pen).queryByText('−30')).toBeNull()
  })

  it('los 7 desplegables con su texto', () => {
    const { container } = render(<ComoFunciona />)
    expect(screen.getByRole('heading', { name: 'De dónde salen los datos' })).toBeInTheDocument()
    const resumenes = [...container.querySelectorAll('details > summary')].map((s) => s.textContent)
    expect(resumenes).toEqual([
      '¿De qué portales vienen los anuncios?',
      '¿Qué municipios se rastrean?',
      '¿Cómo se asegura que el precio es real?',
      '¿Qué significa "barato para su zona"?',
      '¿Por qué algunos salen como "sin valorar"?',
      '¿Qué anuncios se descartan?',
      '¿De dónde vienen los datos del mapa de seguridad?',
    ])
    const textoDe = (i: number) => container.querySelectorAll('details')[i]?.textContent ?? ''
    expect(textoDe(0)).toContain('pisos.com')
    expect(textoDe(0)).toContain('fotocasa')
    expect(textoDe(0)).toContain('las 4 zonas de Madrid, no Toledo Norte')
    expect(textoDe(1)).toContain('Madrid Sur (18) · hasta 300.000 €')
    expect(textoDe(1)).toContain('Torrejón de la Calzada · Valdemoro')
    expect(textoDe(1)).toContain('Madrid Este (6) · hasta 350.000 €')
    expect(textoDe(1)).toContain('Torrejón de Ardoz')
    expect(textoDe(1)).toContain('Madrid Sureste (5) · hasta 300.000 €')
    expect(textoDe(1)).toContain('Rivas-Vaciamadrid')
    expect(textoDe(1)).toContain('Madrid Norte (6) · hasta 400.000 €')
    expect(textoDe(1)).toContain('Tres Cantos')
    expect(textoDe(1)).toContain('Toledo Norte (5) · hasta 300.000 €')
    expect(textoDe(1)).toContain('Esquivias · Illescas · Seseña · Ugena · Yeles')
    expect(textoDe(2)).toContain('tope de su zona')
    expect(textoDe(3)).toContain('segmento asequible')
    expect(textoDe(4)).toContain('"s/valorar"')
    expect(textoDe(5)).toContain('sin posesión')
    expect(textoDe(5)).toContain('nuda propiedad')
    expect(textoDe(5)).toContain('subastas')
    expect(textoDe(6)).toContain('ine.es/experimental/atlas')
    expect(textoDe(6)).toContain('estadisticasdecriminalidad.ses.mir.es')
  })
})
