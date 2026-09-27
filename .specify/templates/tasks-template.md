---

description: "Plantilla de lista de tareas para la implementación de una funcionalidad"
---

# Tareas: [NOMBRE DE LA FUNCIONALIDAD]

**Entrada**: Documentos de diseño en `/specs/[###-nombre-funcionalidad]/`

**Prerrequisitos**: plan.md (obligatorio), spec.md (obligatorio para las historias de usuario), research.md, data-model.md, contracts/

**Tests**: Los ejemplos de abajo incluyen tareas de test. Los tests son OPCIONALES — inclúyelos solo si se piden explícitamente en la especificación de la funcionalidad.

**Organización**: Las tareas se agrupan por historia de usuario para permitir su implementación y testing de forma independiente.

## Formato: `[ID] [P?] [Story] Descripción`

- **[P]**: Se puede ejecutar en paralelo (ficheros distintos, sin dependencias)
- **[Story]**: A qué historia de usuario pertenece la tarea (p. ej. US1, US2, US3)
- Incluye rutas de fichero exactas en las descripciones

## Convenciones de rutas

- **Proyecto único**: `src/`, `tests/` en la raíz del repositorio
- **App web**: `backend/src/`, `frontend/src/`
- **Móvil**: `api/src/`, `ios/src/` o `android/src/`
- Las rutas de abajo asumen proyecto único — ajústalas según la estructura de plan.md

<!--
  ============================================================================
  IMPORTANTE: Las tareas de abajo son TAREAS DE EJEMPLO solo a modo ilustrativo.

  El comando /speckit-tasks DEBE sustituirlas por tareas reales basadas en:
  - Las historias de usuario de spec.md (con sus prioridades P1, P2, P3...)
  - Los requisitos de la funcionalidad de plan.md
  - Las entidades de data-model.md
  - Los endpoints de contracts/

  Las tareas DEBEN organizarse por historia de usuario para que cada una se
  pueda:
  - Implementar de forma independiente
  - Testear de forma independiente
  - Entregar como incremento de MVP

  NO dejes estas tareas de ejemplo en el fichero tasks.md generado.
  ============================================================================
-->

## Fase 1: Configuración (Infraestructura compartida)

**Propósito**: Inicialización del proyecto y estructura básica

- [ ] T001 Crear la estructura del proyecto según el plan de implementación
- [ ] T002 Inicializar el proyecto en [lenguaje] con las dependencias de [framework]
- [ ] T003 [P] Configurar herramientas de linting y formateo

---

## Fase 2: Fundacional (Prerrequisitos bloqueantes)

**Propósito**: Infraestructura núcleo que DEBE estar completa antes de implementar CUALQUIER historia de usuario

**⚠️ CRÍTICO**: Ninguna historia de usuario puede empezar hasta que esta fase esté completa

Ejemplos de tareas fundacionales (ajustar según el proyecto):

- [ ] T004 Configurar el esquema de base de datos y el framework de migraciones
- [ ] T005 [P] Implementar el framework de autenticación/autorización
- [ ] T006 [P] Configurar el enrutado de la API y el middleware
- [ ] T007 Crear los modelos/entidades base de los que dependen todas las historias
- [ ] T008 Configurar la infraestructura de manejo de errores y logging
- [ ] T009 Configurar la gestión de configuración por entorno

**Punto de control**: Fundación lista — puede empezar la implementación de historias de usuario en paralelo

---

## Fase 3: Historia de Usuario 1 - [Título] (Prioridad: P1) 🎯 MVP

**Objetivo**: [Breve descripción de lo que aporta esta historia]

**Test independiente**: [Cómo verificar que esta historia funciona por sí sola]

### Tests de la Historia de Usuario 1 (OPCIONAL — solo si se piden tests) ⚠️

> **NOTA: Escribe estos tests PRIMERO, asegúrate de que FALLAN antes de implementar**

- [ ] T010 [P] [US1] Test de contrato para [endpoint] en tests/contract/test_[nombre].py
- [ ] T011 [P] [US1] Test de integración para [recorrido de usuario] en tests/integration/test_[nombre].py

### Implementación de la Historia de Usuario 1

- [ ] T012 [P] [US1] Crear el modelo [Entidad1] en src/models/[entidad1].py
- [ ] T013 [P] [US1] Crear el modelo [Entidad2] en src/models/[entidad2].py
- [ ] T014 [US1] Implementar [Servicio] en src/services/[servicio].py (depende de T012, T013)
- [ ] T015 [US1] Implementar [endpoint/funcionalidad] en src/[ubicación]/[fichero].py
- [ ] T016 [US1] Añadir validación y manejo de errores
- [ ] T017 [US1] Añadir logging para las operaciones de la historia de usuario 1

**Punto de control**: En este punto, la Historia de Usuario 1 debe ser totalmente funcional y testeable de forma independiente

---

## Fase 4: Historia de Usuario 2 - [Título] (Prioridad: P2)

**Objetivo**: [Breve descripción de lo que aporta esta historia]

**Test independiente**: [Cómo verificar que esta historia funciona por sí sola]

### Tests de la Historia de Usuario 2 (OPCIONAL — solo si se piden tests) ⚠️

- [ ] T018 [P] [US2] Test de contrato para [endpoint] en tests/contract/test_[nombre].py
- [ ] T019 [P] [US2] Test de integración para [recorrido de usuario] en tests/integration/test_[nombre].py

### Implementación de la Historia de Usuario 2

- [ ] T020 [P] [US2] Crear el modelo [Entidad] en src/models/[entidad].py
- [ ] T021 [US2] Implementar [Servicio] en src/services/[servicio].py
- [ ] T022 [US2] Implementar [endpoint/funcionalidad] en src/[ubicación]/[fichero].py
- [ ] T023 [US2] Integrar con los componentes de la Historia de Usuario 1 (si hace falta)

**Punto de control**: En este punto, las Historias de Usuario 1 y 2 deben funcionar ambas de forma independiente

---

## Fase 5: Historia de Usuario 3 - [Título] (Prioridad: P3)

**Objetivo**: [Breve descripción de lo que aporta esta historia]

**Test independiente**: [Cómo verificar que esta historia funciona por sí sola]

### Tests de la Historia de Usuario 3 (OPCIONAL — solo si se piden tests) ⚠️

- [ ] T024 [P] [US3] Test de contrato para [endpoint] en tests/contract/test_[nombre].py
- [ ] T025 [P] [US3] Test de integración para [recorrido de usuario] en tests/integration/test_[nombre].py

### Implementación de la Historia de Usuario 3

- [ ] T026 [P] [US3] Crear el modelo [Entidad] en src/models/[entidad].py
- [ ] T027 [US3] Implementar [Servicio] en src/services/[servicio].py
- [ ] T028 [US3] Implementar [endpoint/funcionalidad] en src/[ubicación]/[fichero].py

**Punto de control**: Todas las historias de usuario deben ser ya funcionales de forma independiente

---

[Añade más fases de historia de usuario según haga falta, siguiendo el mismo patrón]

---

## Fase N: Pulido y aspectos transversales

**Propósito**: Mejoras que afectan a varias historias de usuario

- [ ] TXXX [P] Actualizaciones de documentación en docs/
- [ ] TXXX Limpieza de código y refactorización
- [ ] TXXX Optimización de rendimiento en todas las historias
- [ ] TXXX [P] Tests unitarios adicionales (si se piden) en tests/unit/
- [ ] TXXX Endurecimiento de seguridad
- [ ] TXXX Ejecutar la validación de quickstart.md

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Configuración (Fase 1)**: Sin dependencias — puede empezar de inmediato
- **Fundacional (Fase 2)**: Depende de que Configuración esté completa — BLOQUEA todas las historias de usuario
- **Historias de Usuario (Fase 3+)**: Todas dependen de que la fase Fundacional esté completa
  - Las historias de usuario pueden avanzar en paralelo (si hay recursos)
  - O de forma secuencial en orden de prioridad (P1 → P2 → P3)
- **Pulido (fase final)**: Depende de que las historias de usuario deseadas estén completas

### Dependencias entre historias de usuario

- **Historia de Usuario 1 (P1)**: Puede empezar tras Fundacional (Fase 2) — sin dependencias de otras historias
- **Historia de Usuario 2 (P2)**: Puede empezar tras Fundacional (Fase 2) — puede integrarse con US1 pero debe ser testeable de forma independiente
- **Historia de Usuario 3 (P3)**: Puede empezar tras Fundacional (Fase 2) — puede integrarse con US1/US2 pero debe ser testeable de forma independiente

### Dentro de cada historia de usuario

- Los tests (si se incluyen) DEBEN escribirse y FALLAR antes de implementar
- Modelos antes que servicios
- Servicios antes que endpoints
- Implementación núcleo antes que integración
- Historia completa antes de pasar a la siguiente prioridad

### Oportunidades de paralelización

- Todas las tareas de Configuración marcadas [P] se pueden ejecutar en paralelo
- Todas las tareas Fundacionales marcadas [P] se pueden ejecutar en paralelo (dentro de la Fase 2)
- Una vez completada la fase Fundacional, todas las historias de usuario pueden empezar en paralelo (si hay capacidad de equipo)
- Todos los tests de una historia de usuario marcados [P] se pueden ejecutar en paralelo
- Los modelos dentro de una historia marcados [P] se pueden ejecutar en paralelo
- Distintas historias de usuario pueden trabajarse en paralelo por distintos miembros del equipo

---

## Ejemplo de paralelización: Historia de Usuario 1

```bash
# Lanzar juntos todos los tests de la Historia de Usuario 1 (si se piden tests):
Task: "Test de contrato para [endpoint] en tests/contract/test_[nombre].py"
Task: "Test de integración para [recorrido de usuario] en tests/integration/test_[nombre].py"

# Lanzar juntos todos los modelos de la Historia de Usuario 1:
Task: "Crear el modelo [Entidad1] en src/models/[entidad1].py"
Task: "Crear el modelo [Entidad2] en src/models/[entidad2].py"
```

---

## Estrategia de implementación

### MVP primero (solo Historia de Usuario 1)

1. Completar la Fase 1: Configuración
2. Completar la Fase 2: Fundacional (CRÍTICO — bloquea todas las historias)
3. Completar la Fase 3: Historia de Usuario 1
4. **PARAR Y VALIDAR**: testear la Historia de Usuario 1 de forma independiente
5. Desplegar/hacer demo si está listo

### Entrega incremental

1. Completar Configuración + Fundacional → Fundación lista
2. Añadir Historia de Usuario 1 → testear de forma independiente → Desplegar/Demo (¡MVP!)
3. Añadir Historia de Usuario 2 → testear de forma independiente → Desplegar/Demo
4. Añadir Historia de Usuario 3 → testear de forma independiente → Desplegar/Demo
5. Cada historia añade valor sin romper las anteriores

### Estrategia de equipo en paralelo

Con varios desarrolladores:

1. El equipo completa Configuración + Fundacional juntos
2. Una vez completada la fase Fundacional:
   - Desarrollador/a A: Historia de Usuario 1
   - Desarrollador/a B: Historia de Usuario 2
   - Desarrollador/a C: Historia de Usuario 3
3. Las historias se completan e integran de forma independiente

---

## Notas

- Tareas [P] = ficheros distintos, sin dependencias
- La etiqueta [Story] asocia la tarea a una historia de usuario concreta para trazabilidad
- Cada historia de usuario debe ser completable y testeable de forma independiente
- Verifica que los tests fallan antes de implementar
- Haz commit tras cada tarea o grupo lógico de tareas
- Detente en cualquier punto de control para validar la historia de forma independiente
- Evita: tareas vagas, conflictos sobre el mismo fichero, dependencias entre historias que rompan la independencia
