# Guía de uso de Spec Kit

Este repo usa [Spec Kit](https://github.com/github/spec-kit) (GitHub) como
harness de desarrollo dirigido por especificación ("Spec-Driven
Development", SDD). Los comandos ya están instalados como *skills* de
Claude Code en `.claude/skills/speckit-*/` — no hace falta instalar el CLI
`specify` para usarlos desde aquí, solo invocarlos como `/speckit-<nombre>`.

## ¿Qué es Spec-Driven Development?

La idea de Spec Kit es invertir el orden habitual: en vez de escribir código
primero y documentar (si acaso) después, la especificación se convierte en
el artefacto que **genera** la implementación, no solo en scaffolding que se
descarta. Cada fase produce un documento que la siguiente fase consume:

```
constitución  →  spec  →  plan  →  tasks  →  implementación  →  convergencia
 (principios)   (qué y     (cómo    (pasos     (código real)     (¿queda
                  por qué)  técnico)  concretos)                   trabajo
                                                                    pendiente?)
```

## Flujo de trabajo (orden recomendado)

### 0. `/speckit-constitution` — una vez por proyecto

Define los principios no negociables del proyecto (alcance, calidad,
migraciones, etc.). Ya lo hemos hecho: está en
[`.specify/memory/constitution.md`](.specify/memory/constitution.md).
Solo se vuelve a invocar cuando cambian las reglas de fondo del proyecto,
no para cada feature.

### 1. `/speckit-specify` — qué quieres construir

Describe la funcionalidad en términos de **qué** y **por qué**, sin hablar
todavía de stack técnico. Genera un spec con requisitos e historias de
usuario.

```text
/speckit-specify Quiero una API que sirva los listings de vivienda ya
puntuados, para que el dashboard deje de leer JSON del repo.
```

### 2. `/speckit-clarify` — opcional pero recomendado antes de planificar

Repasa el spec en busca de zonas ambiguas o infra-especificadas y te
pregunta antes de que esas dudas se conviertan en decisiones de diseño
implícitas durante el plan.

### 3. `/speckit-plan` — cómo lo vas a construir

Aquí sí entra el stack técnico y las decisiones de arquitectura.

```text
/speckit-plan Usar FastAPI + PostgreSQL, desplegado en Render; el
dashboard de Streamlit consume la API por HTTP en vez de leer datos/.
```

### 4. `/speckit-tasks` — desglose en pasos accionables

Convierte el plan en una lista de tareas concretas y ordenadas, cada una
lo bastante pequeña como para implementarse y verificarse de una sentada.

### 5. `/speckit-analyze` — opcional, antes de implementar

Comprueba consistencia y cobertura cruzada entre spec, plan y tasks:
detecta huecos (un requisito del spec sin tarea que lo cubra) o
contradicciones entre documentos.

### 6. `/speckit-checklist` — opcional

Genera checklists de calidad a medida para validar que los requisitos
están completos, son claros y no se contradicen — "tests unitarios para
el inglés", como lo describe el propio proyecto.

### 7. `/speckit-implement` — ejecuta las tareas

Implementa las tareas del plan en orden, construyendo la feature real.

### 8. `/speckit-converge` — ¿queda algo pendiente?

Compara el estado real del código contra spec + plan + tasks y añade como
tareas nuevas cualquier cosa que se haya quedado a medias. La recomendación
oficial es repetir **implement → converge** hasta que converge informe
`Converged`.

### Comando adicional: `/speckit-taskstoissues`

Convierte la lista de tareas generada en issues de GitHub, si prefieres
llevar el seguimiento ahí en vez de en los ficheros de `.specify/`.

## Dónde vive cada cosa

- `.specify/memory/constitution.md` — la constitución del proyecto.
- `.specify/scripts/` — scripts auxiliares (PowerShell) que usan los
  comandos internamente (resolución de templates, etc.).
- `.specify/templates/` — plantillas base de spec/plan/tasks; se pueden
  sobreescribir con overrides locales en `.specify/templates/overrides/`
  sin tocar el core.
- `.claude/skills/speckit-*/` — la implementación de cada comando como
  skill de Claude Code.

Cada ciclo de feature (spec → plan → tasks → implement → converge) genera
sus propios ficheros de spec/plan/tasks; consulta la salida de cada comando
para ver dónde los deja exactamente.

## Referencias

- Repositorio: <https://github.com/github/spec-kit>
- Guía detallada paso a paso (en inglés): `spec-driven.md` del propio
  repositorio de Spec Kit.
- Documentación publicada: <https://github.github.io/spec-kit/>
