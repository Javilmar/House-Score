declare module 'plotly.js-dist-min' {
  // Tipado mínimo: solo lo que usa Grafico.tsx.
  export interface Plotly {
    react(
      root: HTMLElement,
      data: unknown[],
      layout?: Record<string, unknown>,
      config?: Record<string, unknown>,
    ): Promise<unknown>
    purge(root: HTMLElement): void
  }
  const Plotly: Plotly
  export default Plotly
}
