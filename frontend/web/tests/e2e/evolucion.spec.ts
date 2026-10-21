import { expect, test } from '@playwright/test'
import { simularApi } from './api-simulada'

test.beforeEach(async ({ page }) => simularApi(page))

test('Evolución y análisis dibuja los 4 gráficos con Plotly', async ({ page }) => {
  const errores: string[] = []
  page.on('pageerror', (e) => errores.push(e.message))

  await page.goto('/#/evolucion')
  await expect(page.getByRole('heading', { level: 3, name: 'Evolución diaria' })).toBeVisible()
  await expect(page.getByRole('heading', { level: 3, name: 'Distribución de scores' })).toBeVisible()
  await expect(page.getByRole('heading', { level: 3, name: 'Top ubicaciones' })).toBeVisible()

  for (const id of [
    'grafico-evolucion-listings',
    'grafico-evolucion-precios',
    'grafico-distribucion-scores',
    'grafico-top-ubicaciones',
  ]) {
    await expect(page.getByTestId(id).locator('.main-svg').first()).toBeAttached({ timeout: 15_000 })
  }
  await expect(page.getByText('Se necesitan al menos 2 días de datos')).toHaveCount(0)
  expect(errores).toEqual([])
})
