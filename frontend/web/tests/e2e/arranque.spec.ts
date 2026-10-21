import { expect, test } from '@playwright/test'
import { simularApi } from './api-simulada'

const TABS: [string, string][] = [
  ['Listados completos', '#/listados'],
  ['Top scoring', '#/top'],
  ['Novedades', '#/novedades'],
  ['Evolución y análisis', '#/evolucion'],
  ['Bajadas de precio', '#/bajadas'],
  ['Hipoteca', '#/hipoteca'],
  ['Cómo funciona', '#/como-funciona'],
  ['Mapas', '#/mapas'],
]

test.beforeEach(async ({ page }) => simularApi(page))

test('arranca, muestra las 8 pestañas y cada una cambia el hash', async ({ page }) => {
  const errores: string[] = []
  page.on('pageerror', (e) => errores.push(e.message))

  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1, name: 'House Score' })).toBeVisible()

  const tabs = page.getByRole('tab')
  await expect(tabs).toHaveCount(8)
  await expect(tabs).toHaveText(TABS.map(([t]) => t))
  await expect(page).toHaveURL(/#\/listados$/)

  for (const [etiqueta, hash] of TABS) {
    await page.getByRole('tab', { name: etiqueta }).click()
    await expect(page).toHaveURL(new RegExp(`${hash}$`))
    await expect(page.getByRole('tab', { name: etiqueta })).toHaveAttribute('aria-selected', 'true')
    await expect(page.getByRole('heading', { level: 2, name: etiqueta })).toBeVisible()
  }
  expect(errores).toEqual([])
})

test('recargar restaura la vista del hash', async ({ page }) => {
  await page.goto('/#/hipoteca?precio=250000')
  await expect(page.getByRole('tab', { name: 'Hipoteca' })).toHaveAttribute('aria-selected', 'true')
  await page.reload()
  await expect(page.getByRole('tab', { name: 'Hipoteca' })).toHaveAttribute('aria-selected', 'true')
  await expect(page).toHaveURL(/#\/hipoteca\?precio=250000$/)
})

test('ruta desconocida → #/listados', async ({ page }) => {
  await page.goto('/#/no-existe')
  await expect(page.getByRole('tab', { name: 'Listados completos' })).toHaveAttribute('aria-selected', 'true')
  await expect(page).toHaveURL(/#\/listados$/)
})
