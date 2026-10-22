import { expect, test } from '@playwright/test'

// Humo contra el front publicado y la API real (T051). Solo lectura: no pulsa nada que
// escriba. Uso: BASE_URL=https://housescore.errinostrich.workers.dev npm run test:smoke

const VISTAS = [
  'Listados completos',
  'Top scoring',
  'Novedades',
  'Evolución y análisis',
  'Bajadas de precio',
  'Hipoteca',
  'Cómo funciona',
  'Mapas',
]

test('carga datos reales y recorre las 8 pestañas sin errores', async ({ page }) => {
  test.setTimeout(240_000)
  const errores: string[] = []
  page.on('pageerror', (e) => errores.push(`pageerror: ${e.message}`))
  page.on('console', (m) => {
    if (m.type() === 'error') errores.push(`console: ${m.text()}`)
  })

  await page.goto('/')
  // La API del plan gratuito puede estar dormida: hasta ~1 min en despertar.
  await expect(page.locator('.kpi-grid')).toBeVisible({ timeout: 120_000 })
  const total = await page.locator('.kpi-card').first().locator('.kpi-value').innerText()
  expect(Number(total.replace(/\D/g, ''))).toBeGreaterThan(0)

  for (const vista of VISTAS) {
    await page.getByRole('tab', { name: vista }).click()
    await expect(page.getByRole('heading', { level: 2, name: vista })).toBeAttached()
  }
  // Mapas descarga sus assets estáticos del propio front.
  await expect(page.locator('.mapas')).toBeVisible()

  expect(errores).toEqual([])
})

test('sirve el favicon', async ({ request }) => {
  const r = await request.get('/favicon.svg')
  expect(r.status()).toBe(200)
  expect(r.headers()['content-type']).toContain('svg')
})
