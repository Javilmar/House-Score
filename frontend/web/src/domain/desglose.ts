/** Desglose de la puntuación (app.py:642-759). */
import { clean } from './derivaciones'

export type CategoriaDesglose =
  | 'valor' | 'tamaño' | 'características' | 'estado' | 'ubicación' | 'mercado' | 'penalización' | 'otro'

export interface ItemDesglose {
  label: string
  points: number
  categoria: CategoriaDesglose
}

export interface Desglose {
  items: ItemDesglose[]
  scoreFinal: number
}

interface ConDetalle {
  score_details: string[]
}

const PENALIZACION = ['⚠️', '🕸️', '❓']
const CARACTERISTICAS = ['🏊', '🚗', '📦', '🌿', '🏡', '🛗', '🌳', '🏗️', '🔧', '🚇', '🏢', '⚡', '📅']
const BONUS = ['💰', '📐', '💎', '📉']
const FEATURE_NAMES: [string, string][] = [
  ['🏊', 'Piscina'], ['🚗', 'Garaje'], ['📦', 'Trastero'], ['🌿', 'Terraza'],
  ['🏡', 'Patio'], ['🛗', 'Ascensor'], ['🌳', 'Jardín'],
]
const PTS_RE = /\s*\(([+-]?\d+)\s*(?:pts)?\)\s*$/
const CAP_RE = /características capadas:\s*(\d+)[→>](\d+)/i

const tiene = (d: string, emojis: string[]) => emojis.some((e) => d.includes(e))
const textos = (p: ConDetalle): string[] => (Array.isArray(p.score_details) ? p.score_details : []).filter((d): d is string => typeof d === 'string')

/** `parse_score_details`: (features, penalties, bonuses) con cada texto pasado por `clean`. */
export function parseScoreDetails(prop: ConDetalle): { features: string[]; penalties: string[]; bonuses: string[] } {
  const features: string[] = []
  const penalties: string[] = []
  const bonuses: string[] = []
  for (const d of textos(prop)) {
    if (tiene(d, PENALIZACION)) penalties.push(clean(d))
    else if (tiene(d, CARACTERISTICAS)) features.push(clean(d))
    else if (tiene(d, BONUS)) bonuses.push(clean(d))
  }
  return { features, penalties, bonuses }
}

function categoria(d: string): CategoriaDesglose {
  if (d.includes('💎') || d.includes('❓')) return 'valor'
  if (d.includes('📐')) return 'tamaño'
  if (tiene(d, ['🏊', '🚗', '📦', '🌿', '🏡', '🛗', '🌳'])) return 'características'
  if (tiene(d, ['🏗️', '🔧', '📅'])) return 'estado'
  if (tiene(d, ['🚇', '🏢', '⚡'])) return 'ubicación'
  if (d.includes('📉') || d.includes('💰')) return 'mercado'
  if (d.includes('⚠️') || d.includes('🕸️')) return 'penalización'
  return 'otro'
}

/** `breakdown_score_details`: ítems {label, points, categoria} reconciliados con el score final. */
export function breakdownScoreDetails(prop: ConDetalle & { score: number }): Desglose {
  const scoreFinal = Math.trunc(Number(prop.score) || 0)
  const items: ItemDesglose[] = []

  for (const d of textos(prop)) {
    const cap = CAP_RE.exec(d)
    if (cap) {
      const raw = Number(cap[1])
      const capped = Number(cap[2])
      items.push({ label: `Características (tope: ${raw}→${capped})`, points: capped - raw, categoria: 'características' })
      continue
    }

    const m = PTS_RE.exec(d)
    const points = m ? Number(m[1]) : 0
    let label = (m ? d.replace(PTS_RE, '') : d).trim()

    for (const [emoji, nombre] of FEATURE_NAMES) {
      if (label.trimEnd() === emoji) {
        label = `${emoji} ${nombre}`
        break
      }
    }
    items.push({ label, points, categoria: categoria(d) })
  }

  const suma = items.reduce((a, it) => a + it.points, 0)
  if (suma !== scoreFinal) {
    const ajuste = scoreFinal - suma
    items.push({ label: 'Ajuste (límite 0-100)', points: ajuste, categoria: ajuste < 0 ? 'penalización' : 'otro' })
  }
  return { items, scoreFinal }
}
