import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['tests/setup.ts'],
    include: ['tests/unit/**/*.test.{ts,tsx}', 'tests/components/**/*.test.{ts,tsx}'],
    // Los tests que montan la App completa renderizan Listados con todo el fixture (~2 s en local);
    // el runner de GitHub Actions es ~2× más lento y rozaba los 5 s por defecto
    testTimeout: 15_000,
  },
})
