import { redondear, scoreColor } from '../domain/derivaciones'

/** Cuadro de score de las tarjetas (`.score-badge`, app.py:1560): `{score:.0f}` sobre `score_color`. */
export default function ScoreBadge({ score }: { score: number }) {
  const s = Number.isFinite(score) ? score : 0
  return (
    <div className="score-badge" style={{ background: scoreColor(s) }}>
      {redondear(s)}
    </div>
  )
}

/** Barra bajo el badge (`.score-bar-track/.score-bar-fill`, app.py:1564). */
export function ScoreBar({ score }: { score: number }) {
  const s = Number.isFinite(score) ? score : 0
  return (
    <div className="score-bar-track">
      <div className="score-bar-fill" style={{ width: `${Math.min(s, 100)}%`, background: scoreColor(s) }} />
    </div>
  )
}
