import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ErrorApi, pedirLista, urlApi } from '../../src/api/cliente'
import { iniciarCarga, type EstadoCarga } from '../../src/state/carga'
import { historicoApi, listingsApi } from '../fixtures'

const API = 'http://api.test'

function respuesta(cuerpo: unknown, status = 200): Response {
  const texto = typeof cuerpo === 'string' ? cuerpo : JSON.stringify(cuerpo)
  return new Response(texto, { status, headers: { 'Content-Type': 'application/json' } })
}

/** fetch que no responde nunca, pero respeta la señal de aborto. */
function fetchColgado() {
  return vi.fn(
    (_url: string | URL | Request, init?: RequestInit) =>
      new Promise<Response>((_res, rej) => {
        init?.signal?.addEventListener('abort', () =>
          rej(init.signal?.reason ?? new DOMException('Aborted', 'AbortError')),
        )
      }),
  )
}

async function error(p: Promise<unknown>): Promise<ErrorApi> {
  try {
    await p
  } catch (e) {
    expect(e).toBeInstanceOf(ErrorApi)
    return e as ErrorApi
  }
  throw new Error('se esperaba un ErrorApi')
}

describe('urlApi', () => {
  it('usa apiUrl sin barra final y compone ruta y parámetros', () => {
    expect(urlApi('/listings', { apiUrl: 'http://x:1/', params: { incluir_retirados: 'true' } })).toBe(
      'http://x:1/listings?incluir_retirados=true',
    )
    expect(urlApi('/historico', { apiUrl: 'http://x:1' })).toBe('http://x:1/historico')
  })
})

describe('pedirLista: clasificación de errores', () => {
  it('200 con lista → la devuelve (una sola petición, solo GET)', async () => {
    const fetchFn = vi.fn().mockResolvedValue(respuesta([{ a: 1 }]))
    await expect(pedirLista('/listings', { apiUrl: API, fetchFn })).resolves.toEqual([{ a: 1 }])
    expect(fetchFn).toHaveBeenCalledTimes(1)
    expect(fetchFn.mock.calls[0]![0]).toBe(`${API}/listings`)
  })

  it('[] no es un error del cliente (lo decide la carga: sin_datos)', async () => {
    const fetchFn = vi.fn().mockResolvedValue(respuesta([]))
    await expect(pedirLista('/listings', { apiUrl: API, fetchFn })).resolves.toEqual([])
  })

  it('fallo de red/CORS (fetch rechaza) → no_disponible con la URL', async () => {
    const fetchFn = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    const e = await error(pedirLista('/listings', { apiUrl: API, fetchFn, params: { x: '1' } }))
    expect(e.tipo).toBe('no_disponible')
    expect(e.url).toBe(`${API}/listings?x=1`)
    expect(e.detalle).toMatch(/conectar/i)
  })

  it('HTTP 429 → limite, sin reintento', async () => {
    const fetchFn = vi.fn().mockResolvedValue(respuesta('', 429))
    const e = await error(pedirLista('/listings', { apiUrl: API, fetchFn }))
    expect(e.tipo).toBe('limite')
    expect(e.url).toBe(`${API}/listings`)
    expect(fetchFn).toHaveBeenCalledTimes(1)
  })

  it('HTTP 503 → http con el código en el detalle', async () => {
    const fetchFn = vi.fn().mockResolvedValue(respuesta('', 503))
    const e = await error(pedirLista('/listings', { apiUrl: API, fetchFn }))
    expect(e.tipo).toBe('http')
    expect(e.detalle).toContain('503')
    expect(fetchFn).toHaveBeenCalledTimes(1)
  })

  it('HTTP 404 y 500 → http', async () => {
    for (const s of [404, 500]) {
      const fetchFn = vi.fn().mockResolvedValue(respuesta('', s))
      const e = await error(pedirLista('/x', { apiUrl: API, fetchFn }))
      expect(e.tipo).toBe('http')
      expect(e.detalle).toContain(String(s))
    }
  })

  it('JSON inválido → ilegible', async () => {
    const fetchFn = vi.fn().mockResolvedValue(respuesta('<html>no json'))
    const e = await error(pedirLista('/listings', { apiUrl: API, fetchFn }))
    expect(e.tipo).toBe('ilegible')
  })

  it('JSON que no es lista, o con elementos que no son objetos → ilegible', async () => {
    for (const cuerpo of [{ a: 1 }, 'texto', 5, null, [1, 2], [{ a: 1 }, null], [[1]]]) {
      const fetchFn = vi.fn().mockResolvedValue(respuesta(JSON.stringify(cuerpo)))
      const e = await error(pedirLista('/listings', { apiUrl: API, fetchFn }))
      expect(e.tipo).toBe('ilegible')
    }
  })
})

describe('temporizadores (fake timers)', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('pedirLista: a los 90 s sin respuesta → no_disponible, y no antes', async () => {
    const fetchFn = fetchColgado()
    let resultado: unknown
    const p = pedirLista('/listings', { apiUrl: API, fetchFn }).catch((e) => (resultado = e))
    await vi.advanceTimersByTimeAsync(89_999)
    expect(resultado).toBeUndefined()
    await vi.advanceTimersByTimeAsync(1)
    await p
    expect(resultado).toBeInstanceOf(ErrorApi)
    expect((resultado as ErrorApi).tipo).toBe('no_disponible')
    expect((resultado as ErrorApi).detalle).toMatch(/tiempo/i)
    expect(fetchFn).toHaveBeenCalledTimes(1)
  })

  function arrancar(fetchFn: typeof fetch) {
    const estados: EstadoCarga[] = []
    const cancelar = iniciarCarga((e) => estados.push(e), { apiUrl: API, fetchFn })
    return { estados, cancelar, ultimo: () => estados[estados.length - 1]! }
  }

  it('cargando → despertando a los 3 s sin respuesta; sigue esperando', async () => {
    const fetchFn = fetchColgado()
    const { estados, ultimo } = arrancar(fetchFn as unknown as typeof fetch)
    expect(ultimo().fase).toBe('cargando')
    await vi.advanceTimersByTimeAsync(2_999)
    expect(ultimo().fase).toBe('cargando')
    await vi.advanceTimersByTimeAsync(1)
    expect(ultimo().fase).toBe('despertando')
    await vi.advanceTimersByTimeAsync(60_000)
    expect(ultimo().fase).toBe('despertando')
    expect(estados.map((e) => e.fase)).toEqual(['cargando', 'despertando'])
  })

  it('despertando → error no_disponible a los 90 s; sin reintentos automáticos', async () => {
    const fetchFn = fetchColgado()
    const { ultimo } = arrancar(fetchFn as unknown as typeof fetch)
    await vi.advanceTimersByTimeAsync(90_000)
    const e = ultimo()
    expect(e).toMatchObject({ fase: 'error', tipo: 'no_disponible' })
    await vi.advanceTimersByTimeAsync(300_000)
    expect(fetchFn).toHaveBeenCalledTimes(2) // /listings y /historico, una vez cada una
  })

  it('respuesta antes de 3 s → listo directamente, sin pasar por despertando', async () => {
    const fetchFn = vi.fn((url: string | URL | Request) =>
      Promise.resolve(respuesta(String(url).includes('/historico') ? historicoApi() : listingsApi())),
    )
    const { estados, ultimo } = arrancar(fetchFn as unknown as typeof fetch)
    await vi.advanceTimersByTimeAsync(0)
    const e = ultimo()
    expect(e.fase).toBe('listo')
    if (e.fase !== 'listo') throw new Error()
    expect(e.listings).toHaveLength(2359)
    expect(e.historico).toHaveLength(50)
    expect(e.listings[0]!.title).toBeTypeOf('string') // ya mapeado a columnas de app.py
    expect(estados.map((x) => x.fase)).toEqual(['cargando', 'listo'])
    expect(fetchFn.mock.calls.map((c) => String(c[0]))).toEqual(
      expect.arrayContaining([`${API}/listings?incluir_retirados=true`, `${API}/historico`]),
    )
    await vi.advanceTimersByTimeAsync(10_000)
    expect(estados.map((x) => x.fase)).toEqual(['cargando', 'listo']) // el aviso de 3 s se cancela
  })

  it('respuesta tras despertar → listo', async () => {
    let soltar: () => void = () => {}
    const puerta = new Promise<void>((r) => (soltar = r))
    const fetchFn = vi.fn(async (url: string | URL | Request) => {
      await puerta
      return respuesta(String(url).includes('/historico') ? [] : listingsApi().slice(0, 3))
    })
    const { ultimo } = arrancar(fetchFn as unknown as typeof fetch)
    await vi.advanceTimersByTimeAsync(5_000)
    expect(ultimo().fase).toBe('despertando')
    soltar()
    await vi.advanceTimersByTimeAsync(0)
    expect(ultimo().fase).toBe('listo')
  })

  it('/listings = [] → sin_datos (distinto de error)', async () => {
    const fetchFn = vi.fn().mockImplementation(() => Promise.resolve(respuesta([])))
    const { ultimo } = arrancar(fetchFn as unknown as typeof fetch)
    await vi.advanceTimersByTimeAsync(0)
    expect(ultimo()).toEqual({ fase: 'sin_datos' })
  })

  it('429 / 503 / JSON ilegible / red → error con tipo y url, sin segundo intento', async () => {
    const casos: [() => Promise<Response>, string][] = [
      [() => Promise.resolve(respuesta('', 429)), 'limite'],
      [() => Promise.resolve(respuesta('', 503)), 'http'],
      [() => Promise.resolve(respuesta('{roto')), 'ilegible'],
      [() => Promise.reject(new TypeError('Failed to fetch')), 'no_disponible'],
    ]
    for (const [fn, tipo] of casos) {
      const fetchFn = vi.fn(fn)
      const { ultimo } = arrancar(fetchFn as unknown as typeof fetch)
      await vi.advanceTimersByTimeAsync(30_000)
      const e = ultimo()
      expect(e).toMatchObject({ fase: 'error', tipo })
      if (e.fase !== 'error') throw new Error()
      expect(e.url).toMatch(/^http:\/\/api\.test\/(listings|historico)/)
      expect(e.detalle).toBeTypeOf('string')
      expect(fetchFn.mock.calls.length).toBeLessThanOrEqual(2)
    }
  })

  it('cancelar impide cualquier estado posterior', async () => {
    const fetchFn = fetchColgado()
    const { estados, cancelar } = arrancar(fetchFn as unknown as typeof fetch)
    cancelar()
    await vi.advanceTimersByTimeAsync(120_000)
    expect(estados.map((e) => e.fase)).toEqual(['cargando'])
  })
})
