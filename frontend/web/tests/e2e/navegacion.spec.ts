import { expect, test, type Page } from '@playwright/test'
import { simularApi } from './api-simulada'

const PESTANAS = [
  ['Listados completos', 'listados'],
  ['Top scoring', 'top'],
  ['Novedades', 'novedades'],
  ['Evolución y análisis', 'evolucion'],
  ['Bajadas de precio', 'bajadas'],
  ['Hipoteca', 'hipoteca'],
  ['Cómo funciona', 'como-funciona'],
  ['Mapas', 'mapas'],
] as const

const TIPOS: Record<string, string> = { 'segunda-mano': 'Segunda mano', 'obra-nueva': 'Obra nueva' }
const CCAAS: Record<string, string> = { madrid: 'Comunidad de Madrid', clm: 'Castilla-La Mancha' }

const digitos = (t: string | null) => Number((t ?? '').replace(/[^\d]/g, ''))

/** Hipoteca abierta con el precio dado y tipo/CCAA igual a los de la URL. */
async function esperarHipotecaPrecargada(page: Page, precio: number) {
  await expect(page.getByRole('tab', { name: 'Hipoteca' })).toHaveAttribute('aria-selected', 'true')
  await expect(page.getByRole('heading', { level: 2, name: 'Hipoteca' })).toBeAttached()
  const params = new URLSearchParams(page.url().split('?')[1])
  expect(Number(params.get('precio'))).toBe(precio)
  await expect(page.getByLabel('Precio de compra (€)')).toHaveValue(String(precio))
  await expect(page.getByRole('radio', { name: TIPOS[params.get('tipo')!]! })).toBeChecked()
  await expect(page.getByRole('radio', { name: CCAAS[params.get('ccaa')!]! })).toBeChecked()
}

// El móvil (390 px) es el caso límite de la especificación: las mismas pruebas a ambos anchos.
for (const ancho of [1280, 390]) {
  test.describe(`navegación a ${ancho} px`, () => {
    test.use({ viewport: { width: ancho, height: 800 } })
    test.beforeEach(async ({ page }) => {
      await simularApi(page)
      await page.route(/basemaps\.cartocdn\.com/, (r) => r.abort())
    })

    test('las 8 pestañas cambian de vista y recargar la conserva', async ({ page }) => {
      await page.goto('/')
      for (const [etiqueta, vista] of PESTANAS) {
        await page.getByRole('tab', { name: etiqueta }).click()
        await expect(page).toHaveURL(new RegExp(`#/${vista}$`))
        await expect(page.getByRole('tab', { name: etiqueta })).toHaveAttribute('aria-selected', 'true')
        await expect(page.getByRole('heading', { level: 2, name: etiqueta })).toBeAttached()

        await page.reload()
        await expect(page.getByRole('tab', { name: etiqueta })).toHaveAttribute('aria-selected', 'true')
        await expect(page.getByRole('heading', { level: 2, name: etiqueta })).toBeAttached()
      }
    })

    test('↗ de Listados abre Top scoring con la tarjeta a la vista y resaltada', async ({ page }) => {
      await page.goto('/#/listados')
      const flecha = page.locator('.list-table button[title="Ver en Top scoring"]').nth(2)
      const href = await flecha.locator('xpath=ancestor::tr').locator('.lt-title a').getAttribute('href')
      await flecha.click()

      await expect(page).toHaveURL(/#\/top\?id=/)
      await expect(page.getByRole('tab', { name: 'Top scoring' })).toHaveAttribute('aria-selected', 'true')
      const tarjeta = page.locator('.prop-card-resaltada')
      await expect(tarjeta).toHaveCount(1)
      await expect(tarjeta.locator('a.prop-title')).toHaveAttribute('href', href!)
      await expect(tarjeta).toBeInViewport()
    })

    test('€ Hipoteca desde Listados precarga precio, tipo y CCAA', async ({ page }) => {
      await page.goto('/#/listados')
      const fila = page.locator('.list-table > tbody > tr').first()
      const precio = digitos(await fila.locator('td.lt-price').textContent())
      await fila.locator('button[title="Calcular hipoteca"]').click()
      await esperarHipotecaPrecargada(page, precio)
    })

    test('€ Hipoteca desde Top scoring precarga precio, tipo y CCAA', async ({ page }) => {
      await page.goto('/#/top')
      const tarjeta = page.locator('.prop-card').nth(1)
      const precio = digitos(await tarjeta.locator('.lc-precio').textContent())
      await tarjeta.getByRole('button', { name: '€ Hipoteca' }).click()
      await esperarHipotecaPrecargada(page, precio)
    })

    test('€ Hipoteca desde Novedades precarga precio, tipo y CCAA', async ({ page }) => {
      await page.goto('/#/novedades')
      const tarjeta = page.locator('.prop-card').first()
      const precio = digitos(await tarjeta.locator('.lc-precio').textContent())
      await tarjeta.getByRole('button', { name: '€ Hipoteca' }).click()
      await esperarHipotecaPrecargada(page, precio)
    })

    test('€ Hipoteca desde Bajadas abre Hipoteca (no Bajadas) con los datos cargados', async ({ page }) => {
      await page.goto('/#/bajadas')
      const tarjeta = page.locator('.prop-card').first()
      const precio = digitos(await tarjeta.locator('.lc-precio').textContent())
      await tarjeta.getByRole('button', { name: '€ Hipoteca' }).click()
      await esperarHipotecaPrecargada(page, precio)
    })
  })
}
