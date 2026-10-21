import { expect, test, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const CORS = { 'Access-Control-Allow-Origin': '*' }
const fixture = (n: string) => readFileSync(resolve(process.cwd(), 'tests/fixtures', n), 'utf8')
const API = 'http://127.0.0.1:8000'

type Respuesta = { status?: number; body?: string; retraso?: number }

/** Responde a /listings y /historico con lo que devuelva `para(ruta, intento)`. */
async function api(page: Page, para: (ruta: 'listings' | 'historico', intento: number) => Respuesta) {
  await page.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.abort())
  const intentos = { listings: 0, historico: 0 }
  for (const ruta of ['listings', 'historico'] as const) {
    await page.route(`${API}/${ruta}**`, async (r) => {
      const { status = 200, body = fixture(`${ruta}.json`), retraso = 0 } = para(ruta, intentos[ruta]++)
      if (retraso) await new Promise((res) => setTimeout(res, retraso))
      await r.fulfill({ status, contentType: 'application/json', headers: CORS, body })
    })
  }
}

const sinCifras = async (page: Page) => {
  await expect(page.locator('.kpi-grid')).toHaveCount(0)
  await expect(page.getByRole('tab')).toHaveCount(0)
  await expect(page.locator('.list-table')).toHaveCount(0)
}

test('respuesta retrasada 10 s: "Despertando el servidor…" y luego los datos', async ({ page }) => {
  await api(page, () => ({ retraso: 10_000 }))
  await page.goto('/')
  await expect(page.getByText('Cargando…')).toBeVisible()
  await expect(page.getByText('Despertando el servidor…')).toBeVisible({ timeout: 8_000 })
  await sinCifras(page)
  await expect(page.getByRole('tab')).toHaveCount(8, { timeout: 15_000 })
  await expect(page.getByText('Despertando el servidor…')).toHaveCount(0)
  await expect(page.locator('.kpi-card')).toHaveCount(6)
})

test('503: aviso con el código y la URL consultada, sin cifras, sin reintento automático', async ({ page }) => {
  let peticiones = 0
  await api(page, (ruta) => {
    if (ruta === 'listings') peticiones++
    return { status: 503, body: '{}' }
  })
  await page.goto('/')
  const alerta = page.getByRole('alert')
  await expect(alerta).toContainText('Error del servidor')
  await expect(alerta).toContainText('HTTP 503')
  await expect(alerta.locator('code')).toContainText(`${API}/listings`)
  await sinCifras(page)
  await page.waitForTimeout(1_500)
  expect(peticiones).toBe(1)
})

test('429: "Demasiadas peticiones" con Reintentar', async ({ page }) => {
  await api(page, () => ({ status: 429, body: '{}' }))
  await page.goto('/')
  const alerta = page.getByRole('alert')
  await expect(alerta).toContainText('Demasiadas peticiones')
  await expect(alerta.getByRole('button', { name: 'Reintentar' })).toBeVisible()
  await sinCifras(page)
})

test('JSON ilegible: "Respuesta ilegible" con la URL', async ({ page }) => {
  await api(page, () => ({ body: '<html>no es json' }))
  await page.goto('/')
  const alerta = page.getByRole('alert')
  await expect(alerta).toContainText('Respuesta ilegible')
  await expect(alerta.locator('code')).toContainText(`${API}/`)
  await sinCifras(page)
})

test('lista vacía: "Sin datos todavía", que no es un error', async ({ page }) => {
  await api(page, () => ({ body: '[]' }))
  await page.goto('/')
  await expect(page.getByText('Sin datos todavía')).toBeVisible()
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Reintentar' })).toBeVisible()
  await sinCifras(page)
})

test('recuperación: tras un fallo, Reintentar vuelve a pedir y muestra los datos', async ({ page }) => {
  await api(page, (_ruta, intento) => (intento === 0 ? { status: 503, body: '{}' } : {}))
  await page.goto('/')
  await page.getByRole('alert').getByRole('button', { name: 'Reintentar' }).click()
  await expect(page.getByRole('tab')).toHaveCount(8)
  await expect(page.locator('.kpi-card')).toHaveCount(6)
  await expect(page.getByRole('alert')).toHaveCount(0)
})

test('recuperación desde "sin datos"', async ({ page }) => {
  await api(page, (_ruta, intento) => (intento === 0 ? { body: '[]' } : {}))
  await page.goto('/')
  await page.getByRole('button', { name: 'Reintentar' }).click()
  await expect(page.getByRole('tab')).toHaveCount(8)
})
