import { expect, test } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { simularApi } from './api-simulada'

const listings: { estado: string }[] = JSON.parse(
  readFileSync(resolve(process.cwd(), 'tests/fixtures/listings.json'), 'utf8'),
)
const ACTIVOS = listings.filter((l) => l.estado !== 'retirado').length

test.beforeEach(async ({ page }) => simularApi(page))

const filas = (page: import('@playwright/test').Page) => page.locator('.list-table > tbody > tr')

test('carga: KPI, tabla con los activos y sus controles', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('.kpi-card')).toHaveCount(6)
  await expect(page.locator('.kpi-card .kpi-value').first()).toHaveText(String(ACTIVOS))
  await expect(filas(page)).toHaveCount(ACTIVOS)
  await expect(page.getByText(`${ACTIVOS} listings · clic en una cabecera`)).toBeVisible()
  await expect(page.getByRole('checkbox', { name: 'Mostrar retirados' })).not.toBeChecked()
})

test('filtrar por zona, mostrar retirados y que el hash lo recuerde', async ({ page }) => {
  await page.goto('/')
  await expect(filas(page)).toHaveCount(ACTIVOS)

  await page.locator('.f-multi', { hasText: 'Elegir opciones' }).first().locator('summary').click()
  await page.getByRole('checkbox', { name: 'Madrid Sur' }).check()
  await expect(page).toHaveURL(/#\/listados\?zona=Madrid\+Sur$/)
  const n = await filas(page).count()
  expect(n).toBeGreaterThan(0)
  expect(n).toBeLessThan(ACTIVOS)
  for (const u of await filas(page).locator('td:nth-child(9)').allTextContents()) expect(u).toBe('Madrid Sur')

  await page.getByRole('checkbox', { name: 'Mostrar retirados' }).check()
  expect(await filas(page).count()).toBeGreaterThan(n)

  // recargar restaura los filtros
  const total = await filas(page).count()
  await page.reload()
  await expect(filas(page)).toHaveCount(total)
  await expect(page.getByRole('checkbox', { name: 'Mostrar retirados' })).toBeChecked()
})

test('ordenar por precio en ambos sentidos', async ({ page }) => {
  await page.goto('/')
  const precios = async () =>
    (await filas(page).locator('td.lt-price').allTextContents()).map((t) => Number(t.replace(/[^\d]/g, '')))
  await expect(filas(page)).toHaveCount(ACTIVOS)
  await page.getByRole('columnheader', { name: /Precio/ }).click()
  const asc = await precios()
  expect(asc).toEqual([...asc].sort((a, b) => a - b))
  await page.getByRole('columnheader', { name: /Precio/ }).click()
  const desc = await precios()
  expect(desc).toEqual([...desc].sort((a, b) => b - a))
  await expect(page.getByRole('columnheader', { name: /Precio/ })).toContainText('▼')
})

test('desplegar el desglose de una fila', async ({ page }) => {
  await page.goto('/')
  const primera = filas(page).first()
  await primera.getByText('Ver desglose de puntuación').click()
  await expect(primera.locator('tr.sb-total')).toBeVisible()
  expect(await primera.locator('tr.sb-row').count()).toBeGreaterThan(0)
})

test('el enlace del título abre el anuncio en pestaña nueva', async ({ page }) => {
  await page.goto('/')
  const enlace = filas(page).first().locator('.lt-title a')
  await expect(enlace).toHaveAttribute('target', '_blank')
  await expect(enlace).toHaveAttribute('rel', 'noopener')
})

test('descargar el CSV de lo filtrado', async ({ page }) => {
  await page.goto('/#/listados?zona=Toledo+Norte')
  await expect(filas(page).first()).toBeVisible()
  const visibles = await filas(page).count()
  const [descarga] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Descargar CSV' }).click(),
  ])
  expect(descarga.suggestedFilename()).toMatch(/^listings_\d{4}-\d{2}-\d{2}\.csv$/)
  const ruta = await descarga.path()
  const lineas = readFileSync(ruta, 'utf8').trimEnd().split('\n')
  expect(lineas[0]).toBe('title,price,score,eur_m2,location,m2,rooms,bathrooms,floor,year_built,energy_rating,source,first_seen,url')
  // las descripciones con saltos de línea van entrecomilladas: al menos una línea por listing
  expect(lineas.length - 1).toBeGreaterThanOrEqual(visibles)
})

test.describe('vista estrecha (390 px)', () => {
  test.use({ viewport: { width: 390, height: 844 } })

  test('sin desbordamiento horizontal de la página; la tabla se desplaza dentro de su contenedor', async ({ page }) => {
    await page.goto('/')
    await expect(filas(page).first()).toBeVisible()
    const doc = await page.locator('html').evaluate((e) => e.scrollWidth)
    const ventana = page.viewportSize()!.width
    expect(doc).toBeLessThanOrEqual(ventana)
    const envoltorio = page.locator('.list-table-wrap')
    const { scroll, ancho } = await envoltorio.evaluate((e) => ({ scroll: e.scrollWidth, ancho: e.clientWidth }))
    expect(scroll).toBeGreaterThan(ancho)
    // controles y KPI siguen siendo utilizables
    await expect(page.getByRole('checkbox', { name: 'Mostrar retirados' })).toBeVisible()
    await expect(page.getByLabel('Rango de score (mínimo)')).toBeVisible()
    await expect(page.locator('.kpi-card').first()).toBeVisible()
    await page.getByRole('columnheader', { name: /Precio/ }).click()
    await expect(page.getByRole('columnheader', { name: /Precio/ })).toContainText('▲')
  })
})
