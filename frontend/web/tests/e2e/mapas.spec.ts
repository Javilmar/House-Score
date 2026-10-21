import { expect, test } from '@playwright/test'
import { simularApi } from './api-simulada'

test.beforeEach(async ({ page }) => {
  await simularApi(page)
  // Teselas del mapa base (CARTO): sin red en el e2e.
  await page.route(/basemaps\.cartocdn\.com/, (r) => r.abort())
})

test('los assets del mapa solo se piden al abrir Mapas', async ({ page }) => {
  const pedidos: string[] = []
  page.on('request', (r) => {
    if (/\.(geojson|csv)(\?|$)/.test(r.url())) pedidos.push(r.url())
  })
  await page.goto('/#/listados')
  await expect(page.getByRole('tab', { name: 'Listados completos' })).toHaveAttribute('aria-selected', 'true')
  expect(pedidos).toEqual([])
  await page.getByRole('tab', { name: 'Mapas' }).click()
  await expect(page.locator('.js-plotly-plot')).toBeVisible()
  expect(pedidos.map((u) => u.split('/').pop()).sort()).toEqual([
    'criminalidad.csv',
    'municipios_zona.geojson',
    'secciones_renta.geojson',
  ])
})

test('el mapa se dibuja y el selector cambia de capa', async ({ page }) => {
  await page.goto('/#/mapas')
  const radios = page.getByRole('radio')
  await expect(radios).toHaveCount(3)
  await expect(page.getByRole('radio', { name: '🔴  Criminalidad · por municipio' })).toBeChecked()

  const mapa = page.locator('.js-plotly-plot')
  await expect(mapa).toBeVisible()
  await expect(mapa.locator('canvas.maplibregl-canvas')).toBeVisible()
  await expect(page.getByRole('heading', { level: 3, name: 'Ranking de peligrosidad' })).toBeVisible()
  await expect(page.getByText('Municipios sin datos oficiales (35 en gris)')).toBeVisible()
  await expect(page.getByText('Portal Estadístico de Criminalidad')).toBeVisible()

  await page.getByRole('radio', { name: '🟢  Renta · por barrio (sección censal)' }).check()
  await expect(page).toHaveURL(/#\/mapas\?capa=renta$/)
  await expect(page.getByRole('heading', { level: 3, name: 'Ranking de barrios por renta' })).toBeVisible()
  await expect(page.getByText('Atlas de Distribución de Renta de los Hogares (ADRH 2023)')).toBeVisible()
  await expect(page.locator('.js-plotly-plot canvas.maplibregl-canvas')).toBeVisible()

  await page.getByRole('radio', { name: '🟡  Precio vivienda · por municipio' }).check()
  await expect(page.getByRole('heading', { level: 3, name: 'Ranking de precio por municipio' })).toBeVisible()
})

test('recargar con capa=renta restaura la capa', async ({ page }) => {
  await page.goto('/#/mapas?capa=renta')
  await expect(page.getByRole('radio', { name: '🟢  Renta · por barrio (sección censal)' })).toBeChecked()
  await expect(page.getByRole('heading', { level: 3, name: 'Ranking de barrios por renta' })).toBeVisible()
})
