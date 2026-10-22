import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import Hipoteca from '../../src/views/Hipoteca'
import { DatosProvider } from '../../src/state/datos'
import type { Listing } from '../../src/types'

const lst = (price: number) => ({ price }) as Listing

function montar(precios: number[] = [100000, 300000, 200000]) {
  return render(
    <DatosProvider listings={precios.map(lst)} historico={[]} hoy="2026-07-21">
      <Hipoteca />
    </DatosProvider>,
  )
}

const precio = () => screen.getByLabelText('Precio de compra (€)') as HTMLInputElement
const cambiar = (el: HTMLElement, v: string | number) => fireEvent.change(el, { target: { value: String(v) } })
const kpi = (label: string) => screen.getByText(label).closest('.kpi-card') as HTMLElement

beforeEach(() => {
  window.location.hash = '#/hipoteca'
})

describe('Hipoteca: controles', () => {
  it('rangos, pasos y valores por defecto literales', () => {
    montar()
    expect(precio()).toHaveAttribute('min', '10000')
    expect(precio()).toHaveAttribute('max', '5000000')
    expect(precio()).toHaveAttribute('step', '5000')
    expect(precio().value).toBe('200000') // mediana de los precios
    const entrada = screen.getByLabelText('Entrada (%)')
    expect(entrada).toHaveAttribute('min', '5')
    expect(entrada).toHaveAttribute('max', '50')
    expect(entrada).toHaveAttribute('step', '1')
    expect((entrada as HTMLInputElement).value).toBe('20')
    const plazo = screen.getByLabelText('Plazo (años)')
    expect(plazo).toHaveAttribute('min', '5')
    expect(plazo).toHaveAttribute('max', '40')
    expect((plazo as HTMLInputElement).value).toBe('30')
    const tin = screen.getByLabelText('Tipo de interés fijo (%)')
    expect(tin).toHaveAttribute('min', '0.5')
    expect(tin).toHaveAttribute('max', '8')
    expect(tin).toHaveAttribute('step', '0.05')
    expect((tin as HTMLInputElement).value).toBe('3')
    expect(screen.getByLabelText('Segunda mano')).toBeChecked()
    expect(screen.getByLabelText('Comunidad de Madrid')).toBeChecked()
  })

  it('sin listings usa 200.000 € por defecto y precio formateado con puntos', () => {
    montar([])
    expect(precio().value).toBe('200000')
    expect(screen.getByText('200.000')).toBeInTheDocument()
  })

  it('la mediana se trunca a entero y ignora precios 0 (faltantes)', () => {
    montar([0, 100001, 100002])
    expect(precio().value).toBe('100001')
  })
})

describe('Hipoteca: botones − / + del campo numérico', () => {
  const botones = () => {
    const campo = precio().closest('.st-num') as HTMLElement
    return {
      menos: within(campo).getByRole('button', { name: 'Disminuir' }),
      mas: within(campo).getByRole('button', { name: 'Aumentar' }),
    }
  }

  it('suman y restan un paso y recalculan el resto', () => {
    montar()
    const { menos, mas } = botones()
    fireEvent.click(mas)
    expect(precio().value).toBe('205000')
    fireEvent.click(menos)
    fireEvent.click(menos)
    expect(precio().value).toBe('195000')
    expect(screen.getByText('195.000')).toBeInTheDocument()
  })

  it('se desactivan en los extremos y no los superan', () => {
    montar()
    cambiar(precio(), 5000000)
    expect(botones().mas).toBeDisabled()
    expect(botones().menos).toBeEnabled()
    cambiar(precio(), 10000)
    expect(botones().menos).toBeDisabled()
    cambiar(precio(), 12000)
    fireEvent.click(botones().menos)
    expect(precio().value).toBe('10000')
  })
})

describe('Hipoteca: resultados', () => {
  it('KPIs y desglose con los valores de calc_hipoteca', () => {
    montar()
    cambiar(precio(), 250000)
    expect(within(kpi('Cuota mensual')).getByText('843 €')).toBeInTheDocument()
    expect(within(kpi('Ahorro necesario')).getByText('69.150 €')).toBeInTheDocument()
    expect(within(kpi('Total intereses')).getByText('103.555 €')).toBeInTheDocument()
    expect(within(kpi('Total desembolso')).getByText('372.705 €')).toBeInTheDocument()
    expect(screen.getByText('Concepto (Segunda mano (ITP))')).toBeInTheDocument()
    expect(screen.getByText('Entrada (20%)')).toBeInTheDocument()
    expect(screen.getByText('ITP (6% — Comunidad de Madrid)')).toBeInTheDocument()
    expect(screen.getByText('Otros gastos (gestoría, notaría, tasación…)')).toBeInTheDocument()
    expect(screen.getByText('Ahorro necesario total')).toBeInTheDocument()
    expect(screen.getByText('50.000 €')).toBeInTheDocument()
    expect(screen.getByText('15.000 €')).toBeInTheDocument()
    expect(screen.getByText('4.150 €')).toBeInTheDocument()
  })

  it('obra nueva + CLM cambia impuestos', () => {
    montar()
    cambiar(precio(), 250000)
    fireEvent.click(screen.getByLabelText('Obra nueva'))
    fireEvent.click(screen.getByLabelText('Castilla-La Mancha'))
    expect(screen.getByText('Concepto (Obra nueva (IVA + AJD))')).toBeInTheDocument()
    expect(screen.getByText('IVA (10%)')).toBeInTheDocument()
    expect(screen.getByText('AJD (1.50% — Castilla-La Mancha)')).toBeInTheDocument()
    expect(within(kpi('Ahorro necesario')).getByText('82.900 €')).toBeInTheDocument()
  })

  it('nota legal literal', () => {
    montar()
    expect(
      screen.getByText(
        'Tipos impositivos orientativos 2024-2026. ITP: C. Madrid 6% / CLM 9%. AJD (obra nueva): C. Madrid 0,75% / CLM 1,5%. IVA obra nueva: 10%. Otros gastos (~1,5% + tasación 400€) son estimaciones. Pueden existir bonificaciones por edad, familia numerosa, VPO, etc.',
      ),
    ).toBeInTheDocument()
  })
})

describe('Hipoteca: gastos mensuales estimados', () => {
  it('desplegable con sliders, defaults y ratio con umbrales', () => {
    montar()
    cambiar(precio(), 250000)
    expect(screen.getByText('Gastos mensuales estimados')).toBeInTheDocument()
    const ing = screen.getByLabelText('Ingresos netos mensuales (€)') as HTMLInputElement
    expect(ing.value).toBe('2500')
    expect(ing).toHaveAttribute('min', '500')
    expect(ing).toHaveAttribute('max', '20000')
    expect(ing).toHaveAttribute('step', '100')
    expect((screen.getByLabelText('Comunidad (€/mes)') as HTMLInputElement).value).toBe('80')
    expect((screen.getByLabelText('IBI mensual (€/mes)') as HTMLInputElement).value).toBe('50')
    expect((screen.getByLabelText('Seguro hogar (€/mes)') as HTMLInputElement).value).toBe('30')
    expect((screen.getByLabelText('Luz + gas (€/mes)') as HTMLInputElement).value).toBe('80')
    expect((screen.getByLabelText('Internet (€/mes)') as HTMLInputElement).value).toBe('35')
    // 843 + 275 = 1118 → 44,7 %
    expect(screen.getByText('1.118 €')).toBeInTheDocument()
    expect(screen.getByText('cuota 843 € + gastos 275 €')).toBeInTheDocument()
    const r = screen.getByText('44.7%')
    expect(r).toHaveStyle({ color: '#f87171' })
    expect(screen.getByText('recomendado < 30 %')).toBeInTheDocument()
    cambiar(ing, 4000) // 27,95 %
    expect(screen.getByText('28.0%')).toHaveStyle({ color: '#4ade80' })
    cambiar(ing, 3000) // 37,27 %
    expect(screen.getByText('37.3%')).toHaveStyle({ color: '#fb923c' })
  })
})

describe('Hipoteca: precarga desde la ruta', () => {
  it('rellena precio, tipo y ccaa', () => {
    window.location.hash = '#/hipoteca?precio=250000&tipo=obra-nueva&ccaa=clm'
    montar()
    expect(precio().value).toBe('250000')
    expect(screen.getByLabelText('Obra nueva')).toBeChecked()
    expect(screen.getByLabelText('Castilla-La Mancha')).toBeChecked()
  })

  it('se aplica una sola vez: las ediciones del usuario no se pisan', () => {
    window.location.hash = '#/hipoteca?precio=250000&tipo=obra-nueva&ccaa=clm'
    montar()
    cambiar(precio(), 300000)
    fireEvent.click(screen.getByLabelText('Segunda mano'))
    act(() => window.dispatchEvent(new Event('hashchange'))) // mismo hash: no re-aplica
    expect(precio().value).toBe('300000')
    expect(screen.getByLabelText('Segunda mano')).toBeChecked()
  })

  it('una nueva navegación con otros parámetros vuelve a precargar', async () => {
    window.location.hash = '#/hipoteca?precio=250000&tipo=obra-nueva&ccaa=clm'
    montar()
    cambiar(precio(), 300000)
    act(() => {
      window.location.hash = '#/hipoteca?precio=180000&tipo=segunda-mano&ccaa=madrid'
    })
    await waitFor(() => expect(precio().value).toBe('180000'))
    expect(screen.getByLabelText('Segunda mano')).toBeChecked()
    expect(screen.getByLabelText('Comunidad de Madrid')).toBeChecked()
  })

  it('parámetros inválidos se ignoran', () => {
    window.location.hash = '#/hipoteca?precio=abc&tipo=xx&ccaa=yy'
    montar()
    expect(precio().value).toBe('200000')
    expect(screen.getByLabelText('Segunda mano')).toBeChecked()
    expect(screen.getByLabelText('Comunidad de Madrid')).toBeChecked()
  })
})
