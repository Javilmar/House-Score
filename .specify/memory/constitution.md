<!--
Sync Impact Report
- Version change: 1.1.0 → 1.1.1 (patch: traducción al español, sin cambios
  de fondo en ningún principio)
- Modified principles: ninguno en sustancia — todo el documento se tradujo
  del inglés al español a petición del propietario del proyecto ("todo el
  harness en español, para tener mayor control"), 2026-09-08. El contenido,
  alcance y obligaciones de cada principio se mantienen idénticos a la
  v1.1.0; solo cambia el idioma.
- Added sections: ninguna
- Removed sections: ninguna
- Follow-up TODOs: el stack de backend sigue intencionadamente sin decidir
  (ver Principio II y "Restricciones de Datos y Despliegue") — se resuelve
  en el futuro spec del backend vía /speckit-plan, no en esta constitución.

Informes previos:
- 1.1.0 (minor): nuevo Principio IV "Test-First Development" (TDD
  obligatorio) tras entrevista con el propietario; Principio II
  reescrito para describir las 3 fases arquitectónicas completas
  (JSON en repo → API+BBDD → front web en Vercel).
- 1.0.1 (patch): todas las referencias a `ai-engineering`/`/ai-*` se
  redirigieron a la cadena de Spec Kit (`/speckit-*`) tras eliminar
  ai-engineering del repositorio.
- 1.0.0 (ratificación inicial): Principios Fundamentales (I-V),
  Restricciones de Datos y Despliegue, Flujo de Desarrollo, Gobernanza.
-->

# Constitución de HouseScore

## Principios Fundamentales

### I. El Motor de Scoring como Única Fuente de Verdad

Existe exactamente un motor de scoring para los listings de vivienda, y
toda superficie (dashboard, futura API, futuro front web) DEBE llamarlo
en vez de reimplementar la lógica de puntuación. Si un listing carece
de datos fiables (p. ej. sin m² fiables), DEBE marcarse como
`datos_insuficientes` y mostrarse como "sin valorar" — el motor NO DEBE
adivinar ni forzar una puntuación a partir de datos incompletos.

Motivo: este proyecto existe para hacer un juicio personal y fiable
sobre los listings. Una puntuación silenciosamente incorrecta es peor
que una puntuación visiblemente ausente, y la lógica de scoring
duplicada acaba divergiendo y mintiendo.

### II. El Desacoplo Front-Datos Es la Migración Activa

Este proyecto tiene tres fases arquitectónicas, y todo cambio no
trivial DEBE evaluarse según a qué fase pertenece — no se añade
trabajo que profundice en una fase que el proyecto está dejando atrás
activamente.

1. **Fase 1 (actual, en proceso de retirada)**: scraper → `guardar.py`
   → JSON commiteado en `frontend/datos/` → Streamlit lee el repo
   directamente. Esto fue un hack de arranque, no un destino.
2. **Fase 2 (siguiente, objetivo activo de la migración)**: una API
   respaldada por una base de datos real sustituye el flujo de datos
   JSON-en-repo. El front de Streamlit se mantiene, pero pasa de leer
   ficheros commiteados en este repositorio a ser cliente de la API.
3. **Fase 3 (estado final declarado)**: Streamlit se sustituye por un
   front web (p. ej. React/Next.js) desplegado en una plataforma como
   Vercel, consumiendo la misma API de la Fase 2. Streamlit es un paso
   intermedio, no la tecnología definitiva de front.

Cada transición de fase es su propio spec (`/speckit-specify`) y no se
arranca de forma oportunista dentro de trabajo no relacionado.

Motivo: expresado por el propietario del proyecto durante la
entrevista de constitución (2026-09-08) — tanto el flujo de
datos-vía-push-al-repo como el propio Streamlit se consideran
transitorios, y el harness no debe optimizar para ninguno de los dos
como si fueran permanentes.

### III. Desarrollo Gateado por el Harness (NO NEGOCIABLE)

Ningún cambio no trivial al front, al motor de scoring, al pipeline de
datos o (cuando exista) al backend se publica sin pasar por la cadena
de Spec Kit (ver [GUIA-SPEC-KIT.md](../../GUIA-SPEC-KIT.md)):
`/speckit-specify → /speckit-plan → /speckit-tasks →
/speckit-implement → /speckit-converge`. Los cambios ad hoc que se
suben directamente a `main` sin spec quedan reservados únicamente para
los commits automáticos diarios de datos (`guardar.py`) — nunca para
cambios de código.

Motivo: este es un proyecto personal mantenido en solitario; sin un
harness que se haga cumplir, "solo un arreglo rápido" es como el
alcance y la calidad se degradan sin que nadie se dé cuenta.

### IV. Desarrollo Guiado por Tests (NO NEGOCIABLE)

Los tests se escriben antes que la implementación y DEBEN fallar
primero (Rojo); después se escribe el código mínimo para que pasen
(Verde); después se refactoriza sin cambiar el comportamiento
(Refactor). Esto aplica a todo código no trivial en cualquier fase del
Principio II: el motor de scoring, el pipeline de datos, la futura API
y el futuro front web por igual. Una tarea de `/speckit-tasks` que
añade o cambia comportamiento no está "hecha" hasta que sus tests
existen y pasan; `/speckit-implement` y `/speckit-converge` tratan la
ausencia de tests como trabajo sin terminar, no como deuda aceptable.

Motivo: el propietario del proyecto eligió explícitamente la opción de
mayor rigor ("TDD, tests obligatorios") durante la entrevista de
constitución (2026-09-08), frente a alternativas más ligeras,
precisamente porque la próxima migración a API + base de datos es
exactamente el tipo de cambio estructural donde la lógica sin testear
falla en silencio y de forma costosa.

### V. Disciplina de Alcance

El alcance del producto queda fijado salvo cambio explícito vía spec:
Madrid Sur (18 municipios) + Toledo Norte (5 municipios), precio ≤
300.000 €, fuentes pisos.com (fiable) e idealista (best-effort).
Toledo capital sigue excluida. Nuevos portales, geografías o techos de
precio requieren un spec (`/speckit-specify`) — nunca se añaden como
efecto colateral de un cambio no relacionado.

Motivo: esta es una herramienta personalizada para la búsqueda de un
único comprador; el scope creep sin control desvirtúa el propósito e
infla el coste de scraping y mantenimiento sin ningún beneficio.

### VI. Corte Duro en las Migraciones (Sin Shims de Compatibilidad)

Toda transición de fase del Principio II DEBE ser una migración dura:
la ruta de datos o de front anterior se elimina, no se mantiene detrás
de un flag "por si acaso". Ningún shim de doble escritura, doble
lectura o compatibilidad hacia atrás sobrevive más allá del PR de
migración — esto aplica tanto al corte JSON→API como, más adelante, al
corte Streamlit→front web. Los datos históricos pueden archivarse,
pero una superficie en ejecución NO DEBE ramificar su comportamiento
según con qué generación de la arquitectura esté hablando.

Motivo: esto refleja la postura previa del proyecto en sus reglas
duras (sin shims de compatibilidad para contenido migrado) y evita que
una migración se quede a medias, que es el modo de fallo más probable
en un proyecto personal en solitario trabajando a través de varias
fases arquitectónicas.

## Restricciones de Datos y Despliegue

- **Objetivo de despliegue actual**: Streamlit Community Cloud
  (front), según las Fases 1/2 del Principio II. Su sustitución por un
  front web (p. ej. Vercel) es la Fase 3 y DEBE capturarse en su
  propio spec cuando arranque — no la implica ni la programa esta
  constitución.
- **Stack del backend**: intencionadamente sin decidir a nivel de
  constitución (lenguaje, framework y base de datos quedan abiertos).
  El spec del backend (`/speckit-specify` + `/speckit-plan`) toma esa
  decisión cuando arranque la Fase 2.
- **Visibilidad de los datos**: los datos de vivienda (precios,
  ubicaciones, puntuaciones) PUEDEN seguir siendo públicos, como hoy —
  no son datos personales sensibles de terceros, y el propietario no
  ha pedido restricciones de acceso. Revisar solo si un futuro spec
  introduce datos que cambien este cálculo.
- **Frescura de los datos**: mientras el flujo basado en repo siga
  activo, el commit automático diario de `guardar.py` sigue siendo el
  único escritor de `frontend/datos/`. Nada de ediciones manuales de
  `frontend/datos/*.json`.
- **Secretos**: cualquier clave de API o credencial de BBDD que
  introduzca la migración de la Fase 2 NO DEBE commitearse en este
  repositorio; usar el gestor de secretos de la plataforma de
  hosting elegida en ese spec.

## Flujo de Desarrollo

Este proyecto sigue la cadena de Spec Kit descrita en
[GUIA-SPEC-KIT.md](../../GUIA-SPEC-KIT.md): `/speckit-specify` produce
el spec aprobado, `/speckit-plan` el enfoque técnico, `/speckit-tasks`
el desglose en tareas (cada una con sus propios tests según el
Principio IV), `/speckit-implement` lo ejecuta, y `/speckit-converge`
cierra la brecha entre el código y el spec. Cada fase arquitectónica
del Principio II (API+BBDD, luego front web) es lo bastante grande
como para merecer su propio ciclo completo
(`specify → clarify → plan → tasks → analyze → implement → converge`)
antes de empezar a implementar.

## Gobernanza

Esta constitución prevalece sobre la práctica ad hoc en este
repositorio. Las enmiendas se hacen editando este fichero vía
`/speckit-constitution`, incrementando la versión según versionado
semántico (MAJOR: se elimina o redefine un principio de forma
incompatible; MINOR: se añade un principio o sección; PATCH:
aclaraciones o redacción), y registrando el cambio en el Sync Impact
Report al principio de este fichero. Un cambio que viole un principio
de aquí no se mergea sin una justificación explícita registrada en un
spec.

**Versión**: 1.1.1 | **Ratificada**: 2026-09-08 | **Última enmienda**: 2026-09-08
