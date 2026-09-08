# Plan de Implementación: [FUNCIONALIDAD]

**Rama**: `[###-nombre-funcionalidad]` | **Fecha**: [FECHA] | **Spec**: [enlace]

**Entrada**: Especificación de la funcionalidad en `/specs/[###-nombre-funcionalidad]/spec.md`

**Nota**: Esta plantilla la rellena el comando `/speckit-plan`; su definición describe el flujo de ejecución.

## Resumen

[Extraer del spec de la funcionalidad: requisito principal + enfoque técnico a partir de la investigación]

## Contexto Técnico

<!--
  ACCIÓN REQUERIDA: Sustituye el contenido de esta sección con los detalles
  técnicos del proyecto. La estructura aquí presentada es orientativa para
  guiar el proceso.
-->

**Lenguaje/Versión**: [p. ej. Python 3.11, Swift 5.9, Rust 1.75 o NEEDS CLARIFICATION]

**Dependencias principales**: [p. ej. FastAPI, UIKit, LLVM o NEEDS CLARIFICATION]

**Almacenamiento**: [si aplica, p. ej. PostgreSQL, CoreData, ficheros o N/A]

**Testing**: [p. ej. pytest, XCTest, cargo test o NEEDS CLARIFICATION]

**Plataforma objetivo**: [p. ej. servidor Linux, iOS 15+, WASM o NEEDS CLARIFICATION]

**Tipo de proyecto**: [p. ej. library/cli/web-service/mobile-app/compiler/desktop-app o NEEDS CLARIFICATION]

**Objetivos de rendimiento**: [específico del dominio, p. ej. 1000 req/s, 10k líneas/s, 60 fps o NEEDS CLARIFICATION]

**Restricciones**: [específico del dominio, p. ej. <200ms p95, <100MB memoria, capaz de funcionar offline o NEEDS CLARIFICATION]

**Escala/Alcance**: [específico del dominio, p. ej. 10k usuarios, 1M líneas de código, 50 pantallas o NEEDS CLARIFICATION]

## Constitution Check

*GATE: Debe superarse antes de la Fase 0 de investigación. Volver a comprobar tras el diseño de la Fase 1.*

[Gates determinados a partir del fichero de la constitución]

## Estructura del Proyecto

### Documentación (esta funcionalidad)

```text
specs/[###-funcionalidad]/
├── plan.md              # Este fichero (salida del comando /speckit-plan)
├── research.md          # Salida de la Fase 0 (comando /speckit-plan)
├── data-model.md        # Salida de la Fase 1 (comando /speckit-plan)
├── quickstart.md        # Salida de la Fase 1 (comando /speckit-plan)
├── contracts/           # Salida de la Fase 1 (comando /speckit-plan)
└── tasks.md             # Salida de la Fase 2 (comando /speckit-tasks - NO lo crea /speckit-plan)
```

### Código fuente (raíz del repositorio)
<!--
  ACCIÓN REQUERIDA: Sustituye el árbol de ejemplo de abajo por la estructura
  concreta de esta funcionalidad. Elimina las opciones no usadas y desarrolla
  la estructura elegida con rutas reales (p. ej. apps/admin,
  packages/algo). El plan entregado no debe incluir las etiquetas de Opción.
-->

```text
# [ELIMINAR SI NO SE USA] Opción 1: Proyecto único (POR DEFECTO)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [ELIMINAR SI NO SE USA] Opción 2: Aplicación web (cuando se detecta "frontend" + "backend")
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [ELIMINAR SI NO SE USA] Opción 3: Móvil + API (cuando se detecta "iOS/Android")
api/
└── [igual que backend arriba]

ios/ o android/
└── [estructura específica de plataforma: módulos de funcionalidad, flujos de UI, tests de plataforma]
```

**Decisión de estructura**: [Documenta la estructura elegida y referencia los
directorios reales capturados arriba]

## Complexity Tracking

> **Rellenar SOLO si Constitution Check tiene violaciones que deban justificarse**

| Violación | Por qué es necesaria | Alternativa más simple descartada porque |
|-----------|-----------------------|-------------------------------------------|
| [p. ej. 4º proyecto] | [necesidad actual] | [por qué 3 proyectos no bastan] |
| [p. ej. patrón Repository] | [problema concreto] | [por qué el acceso directo a BD no basta] |
