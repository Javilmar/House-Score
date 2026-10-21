import { defineConfig } from '@playwright/test'

const baseUrlExterna = process.env.BASE_URL
const baseURL = baseUrlExterna ?? 'http://127.0.0.1:4173'

export default defineConfig({
  testDir: 'tests/e2e',
  reporter: 'list',
  use: { baseURL },
  projects: [
    // API simulada con page.route; sirve el build con `vite preview`.
    { name: 'e2e', testIgnore: /smoke\.spec\.ts/ },
    // Solo lectura, contra BASE_URL (front publicado y API real).
    { name: 'smoke', testMatch: /smoke\.spec\.ts/ },
  ],
  webServer: baseUrlExterna
    ? undefined
    : {
        command: 'npm run build && npm run preview -- --host 127.0.0.1 --port 4173 --strictPort',
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 180_000,
      },
})
