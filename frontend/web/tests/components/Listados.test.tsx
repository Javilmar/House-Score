import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mapearListings } from '../../src/api/mapeo'
import { DatosProvider } from '../../src/state/datos'
import Listados from '../../src/views/Listados'
import { listingsApi } from '../fixtures'
import { listing } from '../helpers'

const HOY = '2026-07-21'

/** Orden de entrada = score descendente (como `cargar_datos`). */
const DATOS = [
  listing({ url: 'https://x/a', title: '🏠 Piso Alfa', price: 300000, score: 90, eur_m2: 3750, m2: 80, rooms: 3, municipio: 'getafe', location: 'Getafe', first_seen: '2026-05-01', source: 'pisos.com', score_details: ['💰 Precio (+90)'] }),
  listing({ url: 'https://x/b', title: 'Piso Beta', price: 120000, score: 80, eur_m2: 1500, m2: 80, rooms: 2, municipio: 'illescas', location: 'Illescas', first_seen: '2026-07-10', source: 'idealista', description: 'Promoción de obra nueva' }),
  listing({ url: 'https://x/c', title: 'Piso Gamma', price: 200000, score: 70, eur_m2: null, m2: 0, rooms: 1, municipio: 'parla', location: 'Parla', first_seen: '2026-07-01', source: 'fotocasa', datos_insuficientes: true }),
  listing({ url: 'https://x/d', title: 'Piso Delta', price: 150000, score: 60, eur_m2: 1900, rooms: 2, municipio: '', location: 'Sitio', first_seen: null, source: 'otra', status: 'delisted' }),
  listing({ url: 'ftp://x/e', title: 'Piso Épsilon', price: 250000, score: 50, eur_m2: 3000, rooms: 4, municipio: 'getafe', location: 'Getafe', first_seen: '2026-06-20' }),
]

function montar(listings = DATOS) {
  return render(
    <DatosProvider listings={listings} historico={[]} hoy={HOY}>
      <Listados />
    </DatosProvider>,
  )
}

const filas = () => [...document.querySelectorAll<HTMLElement>('.list-table > tbody > tr')]
const botones = (titulo: string) => [...document.querySelectorAll('.list-table > tbody button')].filter((b) => b.getAttribute('title') === titulo)
const titulos = () => filas().map((f) => f.querySelector('.lt-title')!.textContent!.replace(/retirado|s\/valorar/g, '').trim())

beforeEach(() => {
  window.history.replaceState(null, '', '/#/listados')
})

describe('Listados: tabla', () => {
  it('encabezado "Listados completos" y las 11 columnas del original', () => {
    montar()
    expect(screen.getByRole('heading', { level: 2, name: 'Listados completos' })).toBeInTheDocument()
    const cabeceras = screen.getAllByRole('columnheader').map((c) => c.textContent)
    expect(cabeceras).toEqual(['', 'Título', 'Precio', 'Score', '€/m²', 'm²', 'Tipo', 'Fuente', 'Ubicación', 'Días', ''])
    expect(screen.getByRole('columnheader', { name: 'Días' })).toHaveAttribute('title', 'Días en mercado')
  })

  it('por defecto oculta retirados y ordena por score descendente con medallas', () => {
    montar()
    expect(titulos()).toEqual(['Piso Alfa', 'Piso Beta', 'Piso Gamma', 'Piso Épsilon'])
    const pos = filas().map((f) => f.querySelector('.lt-pos')!.textContent)
    expect(pos).toEqual(['🥇', '🥈', '🥉', ''])
    expect(screen.getByText('4 listings · clic en una cabecera para ordenar · clic en el título para abrir el anuncio')).toBeInTheDocument()
  })

  it('"Mostrar retirados" añade los retirados con su badge y lo refleja en el hash', async () => {
    const user = userEvent.setup()
    montar()
    await user.click(screen.getByRole('checkbox', { name: 'Mostrar retirados' }))
    expect(titulos()).toHaveLength(5)
    expect(window.location.hash).toBe('#/listados?retirados=1')
    const badge = screen.getByText('retirado')
    expect(badge).toHaveClass('lt-tag', 'lt-usada')
    expect(badge).toHaveAttribute('title', 'Sin apariciones recientes en el scraping')
  })

  it('celdas: título sin emoji, precio, score+barra, €/m², m², tipo, fuente, ubicación y días', () => {
    montar()
    const [a, b, c, e] = filas() as [HTMLElement, HTMLElement, HTMLElement, HTMLElement]
    const celdas = (f: HTMLElement) =>
      [...f.querySelectorAll(':scope > td')].map((t) => t.querySelector('.lt-score-num')?.textContent ?? t.textContent)
    expect(celdas(a).slice(1, 10)).toEqual(['Piso Alfa', '300.000 €', '90', '3.750 €', '80', 'Segunda mano', 'pisos.com', 'Madrid Sur', '81d'])
    expect(celdas(b).slice(1, 10)).toEqual(['Piso Beta', '120.000 €', '80', '1.500 €', '80', 'Obra nueva', 'idealista', 'Toledo Norte', '11d'])
    expect(b.querySelector('.lt-nuevo')).not.toBeNull()
    expect(a.querySelector('.lt-src-pisos')).not.toBeNull()
    expect(b.querySelector('.lt-src-idealista')).not.toBeNull()
    expect(c.querySelector('.lt-src-fotocasa')).not.toBeNull()
    const fill = a.querySelector('.lt-score-fill') as HTMLElement
    expect(fill.style.width).toBe('90%')
    expect(fill.style.background).toBe('rgb(34, 197, 94)')
    // sin €/m² fiable
    expect(celdas(c)[4]).toBe('—')
    // color de los días: >45 rojo, >20 ámbar
    expect((a.querySelectorAll(':scope > td')[9] as HTMLElement).style.color).toBe('rgb(248, 113, 113)')
    expect((e.querySelectorAll(':scope > td')[9] as HTMLElement).style.color).toBe('rgb(251, 191, 36)')
  })

  it('badge s/valorar con su título', () => {
    montar()
    const badge = screen.getByText('s/valorar')
    expect(badge).toHaveClass('lt-tag', 'lt-usada')
    expect(badge).toHaveAttribute('title', 'Sin m² fiable: no valorado')
  })

  it('con retirado y sin valorar a la vez, "retirado" va primero', async () => {
    window.history.replaceState(null, '', '/#/listados?retirados=1')
    montar([listing({ url: 'https://x/z', status: 'delisted', datos_insuficientes: true, score: 1 })])
    const celda = filas()[0]!.querySelector('.lt-title')!
    expect([...celda.querySelectorAll('.lt-tag')].map((t) => t.textContent)).toEqual(['retirado', 's/valorar'])
  })

  it('el título enlaza al anuncio en pestaña nueva; sin http es texto', () => {
    montar()
    const enlace = screen.getByRole('link', { name: 'Piso Alfa' })
    expect(enlace).toHaveAttribute('href', 'https://x/a')
    expect(enlace).toHaveAttribute('target', '_blank')
    expect(enlace).toHaveAttribute('rel', 'noopener')
    expect(screen.queryByRole('link', { name: 'Piso Épsilon' })).toBeNull()
    expect(screen.getByText('Piso Épsilon').tagName).toBe('SPAN')
  })

  it('desglose desplegable por fila', async () => {
    const user = userEvent.setup()
    montar()
    const primera = filas()[0]!
    await user.click(within(primera).getByText('Ver desglose de puntuación'))
    expect(primera.querySelector('tr.sb-total')!.textContent).toBe('Total90')
  })
})

describe('Listados: ordenación por cabecera', () => {
  it('primer clic ascendente, segundo descendente, con flecha', async () => {
    const user = userEvent.setup()
    montar()
    await user.click(screen.getByRole('columnheader', { name: /Precio/ }))
    expect(titulos()).toEqual(['Piso Beta', 'Piso Gamma', 'Piso Épsilon', 'Piso Alfa'])
    expect(screen.getByRole('columnheader', { name: /Precio/ })).toHaveTextContent('Precio ▲')
    expect(screen.getByRole('columnheader', { name: /Precio/ })).toHaveAttribute('aria-sort', 'ascending')
    await user.click(screen.getByRole('columnheader', { name: /Precio/ }))
    expect(titulos()).toEqual(['Piso Alfa', 'Piso Épsilon', 'Piso Gamma', 'Piso Beta'])
    expect(screen.getByRole('columnheader', { name: /Precio/ })).toHaveTextContent('Precio ▼')
  })

  it('cambiar de columna reinicia a ascendente y borra la flecha anterior; las medallas viajan con la fila', async () => {
    const user = userEvent.setup()
    montar()
    await user.click(screen.getByRole('columnheader', { name: /Precio/ }))
    await user.click(screen.getByRole('columnheader', { name: /Título/ }))
    expect(titulos()).toEqual(['Piso Alfa', 'Piso Beta', 'Piso Épsilon', 'Piso Gamma'])
    expect(screen.getByRole('columnheader', { name: /Precio/ })).not.toHaveTextContent('▲')
    expect(screen.getByRole('columnheader', { name: /Precio/ })).not.toHaveAttribute('aria-sort')
    const pos = filas().map((f) => f.querySelector('.lt-pos')!.textContent)
    expect(pos).toEqual(['🥇', '🥈', '', '🥉'])
  })

  it('las columnas de acción no ordenan', async () => {
    const user = userEvent.setup()
    montar()
    await user.click(screen.getAllByRole('columnheader')[0]!)
    expect(titulos()).toEqual(['Piso Alfa', 'Piso Beta', 'Piso Gamma', 'Piso Épsilon'])
  })
})

describe('Listados: botones de acción', () => {
  it('↗ lleva a Top con el id del listing y solo existe entre los 30 primeros', async () => {
    const user = userEvent.setup()
    montar()
    expect(botones('Ver en Top scoring')).toHaveLength(4)
    await user.click(within(filas()[1]!).getByTitle('Ver en Top scoring'))
    expect(window.location.hash).toBe(`#/top?id=${encodeURIComponent('https://x/b')}`)
  })

  it('un listing fuera de los 30 primeros solo tiene el botón €', () => {
    const muchos = Array.from({ length: 32 }, (_, i) => listing({ url: `https://x/${i}`, title: `P${i}`, score: 100 - i }))
    montar(muchos)
    expect(botones('Ver en Top scoring')).toHaveLength(30)
    expect(botones('Calcular hipoteca')).toHaveLength(32)
  })

  it('€ lleva a Hipoteca con precio, tipo y ccaa derivados', async () => {
    const user = userEvent.setup()
    montar()
    await user.click(within(filas()[1]!).getByTitle('Calcular hipoteca'))
    expect(window.location.hash).toBe('#/hipoteca?precio=120000&tipo=obra-nueva&ccaa=clm')
    window.history.replaceState(null, '', '/#/listados')
    act(() => window.dispatchEvent(new HashChangeEvent('hashchange')))
    await user.click(within(filas()[0]!).getByTitle('Calcular hipoteca'))
    expect(window.location.hash).toBe('#/hipoteca?precio=300000&tipo=segunda-mano&ccaa=madrid')
  })
})

describe('Listados: filtros', () => {
  it('orden y rótulos de los controles', () => {
    montar()
    expect(screen.getByRole('checkbox', { name: 'Mostrar retirados' })).not.toBeChecked()
    for (const nombre of ['Zona', 'Municipio']) expect(screen.getByText(nombre)).toBeInTheDocument()
    expect(screen.getByText('Rango de score')).toBeInTheDocument()
    expect(screen.getByText('Rango de precio (€)')).toBeInTheDocument()
    expect(screen.getByText('Habitaciones')).toBeInTheDocument()
  })

  it('valores por defecto: rangos completos de la base (sin retirados)', () => {
    montar()
    expect(screen.getByLabelText('Rango de score (máximo)')).toHaveValue('100')
    expect(screen.getByLabelText('Rango de precio (€) (mínimo)')).toHaveValue('120000')
    expect(screen.getByLabelText('Rango de precio (€) (máximo)')).toHaveValue('300000')
    expect(screen.getByLabelText('Habitaciones (mínimo)')).toHaveValue('1')
    expect(screen.getByLabelText('Habitaciones (máximo)')).toHaveValue('4')
    expect(screen.getByText('120,000 € – 300,000 €')).toBeInTheDocument()
  })

  it('la zona acota las opciones de municipio y filtra la tabla', async () => {
    const user = userEvent.setup()
    montar()
    expect(screen.getByRole('checkbox', { name: 'Parla' })).toBeInTheDocument()
    await user.click(screen.getByRole('checkbox', { name: 'Toledo Norte' }))
    expect(titulos()).toEqual(['Piso Beta'])
    expect(screen.queryByRole('checkbox', { name: 'Parla' })).toBeNull()
    expect(screen.getByRole('checkbox', { name: 'Illescas' })).toBeInTheDocument()
    expect(window.location.hash).toBe('#/listados?zona=Toledo+Norte')
  })

  it('municipio, score y habitaciones se combinan y se escriben en el hash', async () => {
    const user = userEvent.setup()
    montar()
    await user.click(screen.getByRole('checkbox', { name: 'Getafe' }))
    expect(titulos()).toEqual(['Piso Alfa', 'Piso Épsilon'])
    expect(window.location.hash).toBe('#/listados?muni=Getafe')
    const min = screen.getByLabelText('Habitaciones (mínimo)')
    act(() => {
      // simula el arrastre del control
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(min, '4')
      min.dispatchEvent(new Event('input', { bubbles: true }))
    })
    expect(titulos()).toEqual(['Piso Épsilon'])
    expect(window.location.hash).toBe('#/listados?muni=Getafe&hab=4-4')
  })

  it('el hash inicial restaura los filtros', () => {
    window.history.replaceState(null, '', '/#/listados?zona=Madrid+Sur&score=85-100&retirados=1')
    montar()
    expect(titulos()).toEqual(['Piso Alfa'])
    expect(screen.getByRole('checkbox', { name: 'Mostrar retirados' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'Madrid Sur' })).toBeChecked()
    expect(screen.getByLabelText('Rango de score (mínimo)')).toHaveValue('85')
  })

  it('sin resultados: "No hay listados con esos filtros." y 0 listings', () => {
    window.history.replaceState(null, '', '/#/listados?score=0-10')
    montar()
    expect(screen.getByText('No hay listados con esos filtros.')).toBeInTheDocument()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.getByText(/^0 listings/)).toBeInTheDocument()
  })
})

describe('Listados: CSV', () => {
  it('descarga los listings filtrados como listings_<fecha>.csv', async () => {
    const user = userEvent.setup()
    window.history.replaceState(null, '', '/#/listados?zona=Toledo+Norte')
    const blobs: Blob[] = []
    URL.createObjectURL = vi.fn((b: Blob | MediaSource) => {
      blobs.push(b as Blob)
      return 'blob:csv'
    })
    URL.revokeObjectURL = vi.fn()
    const nombres: string[] = []
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      nombres.push(this.download)
    })
    montar()
    await user.click(screen.getByRole('button', { name: 'Descargar CSV' }))
    expect(click).toHaveBeenCalledTimes(1)
    expect(nombres).toEqual(['listings_2026-07-21.csv'])
    const csv = await blobs[0]!.text()
    const [cab, ...resto] = csv.trimEnd().split('\n')
    expect(cab).toBe('title,price,score,eur_m2,location,m2,rooms,bathrooms,floor,year_built,energy_rating,source,first_seen,url')
    expect(resto).toEqual(['Piso Beta,120000,80,1500,Illescas,80,2,1,,0,,idealista,2026-07-10,https://x/b'])
    click.mockRestore()
  })
})

describe('Listados: con los datos reales', () => {
  it('renderiza el fixture sin errores y con el recuento esperado', () => {
    const todos = mapearListings(listingsApi())
    montar(todos)
    const activos = todos.filter((l) => l.status !== 'delisted').length
    expect(screen.getByText(new RegExp(`^${activos} listings`))).toBeInTheDocument()
    expect(filas()).toHaveLength(activos)
  })
})
