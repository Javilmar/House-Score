import { ICON_PATHS } from './iconPaths'

export const ICON_NAMES = Object.keys(ICON_PATHS)

interface Props {
  name: string
  size?: number
  color?: string
  stroke?: number
}

/** `icon()` de app.py:85. Nombre desconocido → svg vacío. */
export default function Icon({ name, size = 16, color = 'currentColor', stroke = 1.75 }: Props) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ verticalAlign: '-2px', flexShrink: 0 }}
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: ICON_PATHS[name] ?? '' }}
    />
  )
}
