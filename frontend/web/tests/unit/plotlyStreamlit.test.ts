import { describe, expect, it } from 'vitest'
import { conTemaStreamlit, conTemaStreamlitDatos } from '../../src/styles/plotlyStreamlit'

describe('conTemaStreamlit (plantilla de st.plotly_chart)', () => {
  it('título en negrita alineado a la izquierda', () => {
    const l = conTemaStreamlit({ title: { text: 'Evolución', font: { size: 16 } } }) as { title: Record<string, unknown> }
    expect(l.title).toMatchObject({ text: '<b>Evolución</b>', x: 0, xanchor: 'left', pad: { l: 4 }, font: { size: 16 } })
  })

  it('no duplica la negrita ni crea título si la figura no lo tiene', () => {
    expect((conTemaStreamlit({ title: { text: '<b>A</b>' } }).title as { text: string }).text).toBe('<b>A</b>')
    expect(conTemaStreamlit({}).title).toBeUndefined()
    expect(conTemaStreamlit(undefined).margin).toEqual({ pad: 8 })
  })

  it('ejes con márgenes automáticos y separación de título 20 (x) / 24 (y), incl. ejes secundarios', () => {
    const l = conTemaStreamlit({ xaxis: { showgrid: false }, yaxis: {}, yaxis2: { overlaying: 'y' } }) as Record<string, Record<string, unknown>>
    expect(l.xaxis).toMatchObject({ showgrid: false, automargin: true, tickfont: { color: '#e6eaf1' }, title: { standoff: 20 } })
    expect(l.yaxis).toMatchObject({ automargin: true, title: { standoff: 24 } })
    expect(l.yaxis2).toMatchObject({ overlaying: 'y', automargin: true, title: { standoff: 24 } })
  })

  it('lo que fija la figura prevalece y los mapas no reciben ejes', () => {
    const l = conTemaStreamlit({ margin: { l: 12, r: 12 }, legend: { font: { size: 11 } }, mapbox: { zoom: 8 } }) as Record<string, Record<string, unknown>>
    expect(l.margin).toEqual({ pad: 8, l: 12, r: 12 })
    expect(l.legend!.font).toEqual({ color: '#fafafa', size: 11 })
    expect(l.xaxis).toBeUndefined()
    expect(l.mapbox).toEqual({ zoom: 8 })
    expect(conTemaStreamlit({ legend: { font: { color: 'red' } } }).legend).toEqual({ font: { color: 'red' } })
  })
})

describe('conTemaStreamlit: detalles de ejes', () => {
  it('un título indefinido en la figura no borra la separación de la plantilla', () => {
    const l = conTemaStreamlit({ yaxis: { title: undefined, showgrid: true } }) as Record<string, Record<string, unknown>>
    expect(l.yaxis).toMatchObject({ showgrid: true, title: { standoff: 24, font: { color: '#e6eaf1' } } })
  })

  it('un eje superpuesto fija sus marcas en automático (no se sincronizan con el principal)', () => {
    const l = conTemaStreamlit({ yaxis: {}, yaxis2: { overlaying: 'y', side: 'right' } }) as Record<string, Record<string, unknown>>
    expect(l.yaxis2!.tickmode).toBe('auto')
    expect(l.yaxis!.tickmode).toBeUndefined()
  })
})

describe('conTemaStreamlitDatos', () => {
  it('añade a la barra de color la separación y el contorno transparente de Streamlit sin pisar lo explícito', () => {
    const [a, b] = conTemaStreamlitDatos([{ type: 'choroplethmap', colorbar: { thickness: 10, xpad: 4 } }, { type: 'bar' }]) as Record<string, unknown>[]
    expect(a!.colorbar).toEqual({ xpad: 4, outlinewidth: 8, outlinecolor: 'transparent', thickness: 10 })
    expect(b).toEqual({ type: 'bar' })
  })
})
