# Especificación de Funcionalidad: [NOMBRE DE LA FUNCIONALIDAD]

**Rama de la funcionalidad**: `[###-nombre-funcionalidad]`

**Creada**: [FECHA]

**Estado**: Borrador

**Entrada**: Descripción del usuario: "$ARGUMENTS"

## User Scenarios & Testing *(obligatorio)*

<!--
  IMPORTANTE: Las historias de usuario deben PRIORIZARSE como recorridos de
  usuario ordenados por importancia.
  Cada historia/recorrido de usuario debe ser INDEPENDIENTEMENTE TESTEABLE:
  si implementas solo UNA de ellas, debe seguir siendo un MVP viable
  (Producto Mínimo Viable) que aporte valor.

  Asigna prioridades (P1, P2, P3, etc.) a cada historia, donde P1 es la más
  crítica. Piensa en cada historia como una porción autónoma de
  funcionalidad que se pueda:
  - Desarrollar de forma independiente
  - Testear de forma independiente
  - Desplegar de forma independiente
  - Demostrar a usuarios de forma independiente
-->

### Historia de Usuario 1 - [Título breve] (Prioridad: P1)

[Describe este recorrido de usuario en lenguaje llano]

**Por qué esta prioridad**: [Explica el valor y por qué tiene este nivel de prioridad]

**Test independiente**: [Describe cómo se puede testear de forma independiente — p. ej. "Se puede testear por completo mediante [acción concreta] y aporta [valor concreto]"]

**Acceptance Scenarios**:

1. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado]
2. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado]

---

### Historia de Usuario 2 - [Título breve] (Prioridad: P2)

[Describe este recorrido de usuario en lenguaje llano]

**Por qué esta prioridad**: [Explica el valor y por qué tiene este nivel de prioridad]

**Test independiente**: [Describe cómo se puede testear de forma independiente]

**Acceptance Scenarios**:

1. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado]

---

### Historia de Usuario 3 - [Título breve] (Prioridad: P3)

[Describe este recorrido de usuario en lenguaje llano]

**Por qué esta prioridad**: [Explica el valor y por qué tiene este nivel de prioridad]

**Test independiente**: [Describe cómo se puede testear de forma independiente]

**Acceptance Scenarios**:

1. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado]

---

[Añade más historias de usuario según haga falta, cada una con su prioridad asignada]

### Edge Cases

<!--
  ACCIÓN REQUERIDA: El contenido de esta sección son placeholders.
  Rellénalos con los edge cases correctos.
-->

- ¿Qué ocurre cuando [condición límite]?
- ¿Cómo gestiona el sistema [escenario de error]?

## Requirements *(obligatorio)*

<!--
  ACCIÓN REQUERIDA: El contenido de esta sección son placeholders.
  Rellénalos con los requisitos funcionales correctos.
-->

### Functional Requirements

- **FR-001**: El sistema DEBE [capacidad concreta, p. ej. "permitir a los usuarios crear cuentas"]
- **FR-002**: El sistema DEBE [capacidad concreta, p. ej. "validar direcciones de email"]
- **FR-003**: Los usuarios DEBEN poder [interacción clave, p. ej. "restablecer su contraseña"]
- **FR-004**: El sistema DEBE [requisito de datos, p. ej. "persistir las preferencias del usuario"]
- **FR-005**: El sistema DEBE [comportamiento, p. ej. "registrar todos los eventos de seguridad"]

*Ejemplo de cómo marcar requisitos poco claros:*

- **FR-006**: El sistema DEBE autenticar usuarios mediante [NEEDS CLARIFICATION: método de autenticación no especificado - ¿email/contraseña, SSO, OAuth?]
- **FR-007**: El sistema DEBE conservar los datos de usuario durante [NEEDS CLARIFICATION: periodo de retención no especificado]

### Key Entities *(incluir si la funcionalidad implica datos)*

- **[Entidad 1]**: [Qué representa, atributos clave sin detalles de implementación]
- **[Entidad 2]**: [Qué representa, relaciones con otras entidades]

## Success Criteria *(obligatorio)*

<!--
  ACCIÓN REQUERIDA: Define criterios de éxito medibles.
  Deben ser agnósticos de tecnología y medibles.
-->

### Measurable Outcomes

- **SC-001**: [Métrica medible, p. ej. "los usuarios pueden completar el alta de cuenta en menos de 2 minutos"]
- **SC-002**: [Métrica medible, p. ej. "el sistema soporta 1000 usuarios concurrentes sin degradación"]
- **SC-003**: [Métrica de satisfacción de usuario, p. ej. "el 90% de los usuarios completa la tarea principal a la primera"]
- **SC-004**: [Métrica de negocio, p. ej. "reducir en un 50% los tickets de soporte relacionados con [X]"]

## Assumptions

<!--
  ACCIÓN REQUERIDA: El contenido de esta sección son placeholders.
  Rellénalos con los supuestos correctos, basados en valores por defecto
  razonables cuando la descripción de la funcionalidad no especificaba
  ciertos detalles.
-->

- [Supuesto sobre usuarios objetivo, p. ej. "los usuarios tienen conexión a internet estable"]
- [Supuesto sobre límites de alcance, p. ej. "el soporte móvil queda fuera de alcance para la v1"]
- [Supuesto sobre datos/entorno, p. ej. "se reutilizará el sistema de autenticación existente"]
- [Dependencia de un sistema/servicio existente, p. ej. "requiere acceso a la API de perfil de usuario existente"]
