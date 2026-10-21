import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import type { Page } from '@playwright/test'

const CORS = { 'Access-Control-Allow-Origin': '*' }
const fixture = (n: string) => readFileSync(resolve(process.cwd(), 'tests/fixtures', n), 'utf8')

/** API simulada: sirve los fixtures reales con `page.route` (URL por defecto del build). */
export async function simularApi(page: Page): Promise<void> {
  await page.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.abort())
  await page.route('http://127.0.0.1:8000/listings**', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', headers: CORS, body: fixture('listings.json') }),
  )
  await page.route('http://127.0.0.1:8000/historico**', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', headers: CORS, body: fixture('historico.json') }),
  )
}
