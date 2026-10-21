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

  it('los 6 bloques de scoring con sus filas y colores', () => {
    render(<ComoFunciona />)
    const titulos = [
      '💎 Valor vs zona',
      '📐 Superficie',
      '📈 Señales de mercado',
      '✨ Características',
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
      expect(within(sup).getByText(p)).toBeInTheDocument()
    }

    const mercado = bloque('📈 Señales de mercado')
    expect(within(mercado).getByText('📉 Ha bajado de precio')).toBeInTheDocument()
    expect(within(mercado).getByText('+1 a +5')).toBeInTheDocument()
    expect(within(mercado).getByText('🕸️ Lleva > 45 días anunciado')).toBeInTheDocument()
    expect(within(mercado).getByText('−3')).toBeInTheDocument()
    expect(within(mercado).getByText('−5')).toBeInTheDocument()

    const car = bloque('✨ Características')
    expect(within(car).getByText('Detectadas en anuncio y ficha · el total se limita a +15')).toBeInTheDocument()
    expect(within(car).getByText('🏊 Piscina')).toBeInTheDocument()
    expect(within(car).getByText('máx +15')).toHaveStyle({ color: '#818cf8' })
    expect(within(car).getByText('🌿 Terraza / 🏡 Patio')).toBeInTheDocument()

    const extras = bloque('➕ Extras (suman)')
    expect(within(extras).getByText('⚡ Eficiencia energética A/B/C')).toBeInTheDocument()
    expect(within(extras).getByText('🏗️ Obra nueva / a estrenar')).toBeInTheDocument()

    const pen = bloque('⚠️ Penalizaciones (restan)')
    expect(within(pen).getByText('−30')).toBeInTheDocument()
    expect(within(pen).getByText('−3 a −20')).toBeInTheDocument()
  })

  it('los 6 desplegables con su texto', () => {
    const { container } = render(<ComoFunciona />)
    expect(screen.getByRole('heading', { name: 'De dónde salen los datos' })).toBeInTheDocument()
    const resumenes = [...container.querySelectorAll('details > summary')].map((s) => s.textContent)
    expect(resumenes).toEqual([
      '¿De qué portales vienen los anuncios?',
      '¿Qué municipios se rastrean?',
      '¿Cómo se asegura que el precio es real?',
      '¿Qué significa "barato para su zona"?',
      '¿Por qué algunos salen como "sin valorar"?',
      '¿De dónde vienen los datos del mapa de seguridad?',
    ])
    const textoDe = (i: number) => container.querySelectorAll('details')[i]?.textContent ?? ''
    expect(textoDe(0)).toContain('pisos.com')
    expect(textoDe(0)).toContain('Fotocasa')
    expect(textoDe(1)).toContain('Madrid Sur (18)')
    expect(textoDe(1)).toContain('Torrejón de la Calzada · Valdemoro')
    expect(textoDe(1)).toContain('Toledo Norte (5)')
    expect(textoDe(1)).toContain('Esquivias · Illescas · Seseña · Ugena · Yeles')
    expect(textoDe(2)).toContain('300.000 €')
    expect(textoDe(3)).toContain('segmento asequible')
    expect(textoDe(4)).toContain('"s/valorar"')
    expect(textoDe(5)).toContain('ine.es/experimental/atlas')
    expect(textoDe(5)).toContain('estadisticasdecriminalidad.ses.mir.es')
  })
})
