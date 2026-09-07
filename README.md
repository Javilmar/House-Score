# Dashboard de Búsqueda de Vivienda

Dashboard en Streamlit que visualiza listings de vivienda (Madrid Sur + Toledo
Norte) con scoring a medida. Los datos los genera periódicamente un script en el
ordenador local y se publican a este repo para que el dashboard en la nube
siempre muestre lo último.

## Estructura

```
house-dashboard/
├── dashboard/app.py        # la app Streamlit
├── dashboard/guardar.py    # guarda una pasada y empuja los datos a GitHub
├── datos/                  # JSON diarios (los lee el dashboard)
└── requirements.txt
```

## Ver en local

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Desplegar en Streamlit Community Cloud (gratis)

1. Sube este repo a GitHub.
2. Entra en https://share.streamlit.io con tu cuenta de GitHub.
3. **New app** → elige el repo, rama `main`, y **Main file path** = `dashboard/app.py`.
4. Deploy. Obtienes una URL pública (`tu-app.streamlit.app`).

Cada vez que el script local empuja datos nuevos (ver abajo), Streamlit
redespliega solo y muestra lo último — funcione o no tu ordenador.

## Actualización automática de datos

El script periódico que ya corre en local termina llamando a `guardar.py`, que
escribe el JSON del día y hace `git commit` + `git push` automáticamente. No hay
nada manual que hacer tras el primer despliegue.

## Acceso privado (opcional)

Si no quieres que los datos sean públicos, pon el repo en privado y añade una
contraseña en Streamlit Cloud vía `Settings → Secrets`.

## Harness de desarrollo con IA

Este repo usa **Claude Code** con el framework **ai-engineering** para asistir
en el desarrollo. Al clonar el repo en otro ordenador, estos ficheros ya
traen todo lo necesario para seguir trabajando igual:

- `CLAUDE.md` / `AGENTS.md` — rulebook canónico: cómo debe operar la IA en
  este repo (flujo de trabajo, reglas de commits, principios de ingeniería).
- `.claude/skills/` y `.claude/agents/` — comandos `/ai-*` (brainstorm, plan,
  build, review, verify, etc.) y agentes especializados.
- `.ai-engineering/` — config, overrides por lenguaje, políticas y estado del
  framework. `LESSONS.md` y `specs/` están aún vacíos (sin decisiones
  formales registradas todavía).
- `.codex/`, `.agents/`, `.github/`, `.cursor/`, `.opencode/` — mirrors del
  mismo rulebook para otros IDEs/agentes.

No hace falta instalar nada aparte: son ficheros de configuración/instrucciones
que Claude Code (u otro IDE compatible) lee automáticamente al abrir el repo.

## Decisiones de producto más importantes

(detalle completo en [`dashboard/FUNCIONALIDADES.md`](dashboard/FUNCIONALIDADES.md))

- **Precio máximo scrapeado:** ≤ 300.000 €.
- **Fuentes:** pisos.com (fiable) + idealista (best-effort, puede bloquear
  DataDome).
- **Zona de cobertura:** Madrid Sur (18 municipios) + Toledo Norte (5
  municipios de interés activo). **Toledo capital queda excluida** (>55 min,
  mercado distinto).
- **Motor de scoring único** en `property_scorer.py` (0–100 puntos); si un
  listing no tiene m² fiable se marca `datos_insuficientes` y queda
  "sin valorar" en vez de forzar un cálculo erróneo.
- **Flujo de datos:** scraper → `guardar.py` (merge + detección de bajadas de
  precio + `git commit/push` automático) → `datos/YYYY-MM-DD.json` →
  `app.py` (Streamlit).
- **Diseño:** modo oscuro siempre, un único color de acento (`#6366f1`), sin
  emojis en la UI (se usan iconos SVG Lucide vía `icon()`).
- **Sin dependencias nuevas** salvo justificación explícita — stack actual:
  `streamlit`, `pandas`, `plotly`, `requests`, stdlib Python.
