# Dashboard de Búsqueda de Vivienda

Dashboard en Streamlit que visualiza listings de vivienda (Madrid Sur + Toledo
Norte) con scoring a medida. Los datos los genera periódicamente un script en el
ordenador local y se publican a este repo para que el dashboard en la nube
siempre muestre lo último.

## Estructura

```
HouseScore/
├── frontend/
│   ├── dashboard/app.py        # la app Streamlit
│   ├── dashboard/guardar.py    # guarda una pasada y empuja los datos a GitHub
│   ├── datos/                  # JSON diarios (los lee el dashboard)
│   ├── config/                 # precios de referencia por municipio
│   └── requirements.txt
└── backend/                    # reservado — API + BBDD, aún sin implementar
```

Front y backend son directorios hermanos en el mismo repo (monorepo): un
commit puede tocar ambos a la vez cuando cambia un contrato entre ellos, y
cada uno se despliega apuntando a su propio subdirectorio (Streamlit Cloud →
`frontend/`, hosting de la API → `backend/`). El backend está reservado
pero vacío: la migración de `frontend/datos/*.json` a API + base de datos
necesita su propio spec antes de implementarse — ver
[GUIA-SPEC-KIT.md](GUIA-SPEC-KIT.md) y
[.specify/memory/constitution.md](.specify/memory/constitution.md)
(principios II y V).

## Ver en local

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/dashboard/app.py
```

## Desplegar en Streamlit Community Cloud (gratis)

1. Sube este repo a GitHub.
2. Entra en https://share.streamlit.io con tu cuenta de GitHub.
3. **New app** → elige el repo, rama `main`, y **Main file path** =
   `frontend/dashboard/app.py`.
4. Deploy. Obtienes una URL pública (`tu-app.streamlit.app`).

> Si la app ya estaba desplegada antes de este cambio de estructura, entra en
> **Settings → General** de la app en Streamlit Cloud y actualiza el
> **Main file path** al de arriba — si no, el deploy fallará al no encontrar
> `dashboard/app.py` en la raíz.

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

Este repo usa **Claude Code** con **[Spec Kit](https://github.com/github/spec-kit)**
como harness de desarrollo dirigido por especificación. Ver
[GUIA-SPEC-KIT.md](GUIA-SPEC-KIT.md) para el flujo completo. Los ficheros
relevantes:

- `.specify/memory/constitution.md` — principios no negociables del proyecto.
- `.specify/templates/`, `.specify/scripts/` — plantillas y scripts internos
  de Spec Kit.
- `.claude/skills/speckit-*/` — comandos `/speckit-*` (constitution, specify,
  plan, tasks, implement, converge, clarify, analyze, checklist,
  taskstoissues).

No hace falta instalar nada aparte: son ficheros de configuración/instrucciones
que Claude Code (u otro IDE compatible con Spec Kit) lee automáticamente al
abrir el repo.

## Decisiones de producto más importantes

(detalle completo en [`frontend/dashboard/FUNCIONALIDADES.md`](frontend/dashboard/FUNCIONALIDADES.md))

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
  precio + `git commit/push` automático) → `frontend/datos/YYYY-MM-DD.json` →
  `app.py` (Streamlit).
- **Diseño:** modo oscuro siempre, un único color de acento (`#6366f1`), sin
  emojis en la UI (se usan iconos SVG Lucide vía `icon()`).
- **Sin dependencias nuevas** salvo justificación explícita — stack actual:
  `streamlit`, `pandas`, `plotly`, `requests`, stdlib Python.
