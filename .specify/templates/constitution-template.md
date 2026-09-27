# Constitución de [NOMBRE_PROYECTO]
<!-- Ejemplo: Constitución de Spec, Constitución de TaskFlow, etc. -->

## Principios Fundamentales

### [NOMBRE_PRINCIPIO_1]
<!-- Ejemplo: I. Library-First -->
[DESCRIPCION_PRINCIPIO_1]
<!-- Ejemplo: Toda funcionalidad empieza como una librería autónoma; las librerías deben ser autocontenidas, testeables de forma independiente, documentadas; se requiere un propósito claro - nada de librerías puramente organizativas -->

### [NOMBRE_PRINCIPIO_2]
<!-- Ejemplo: II. Interfaz CLI -->
[DESCRIPCION_PRINCIPIO_2]
<!-- Ejemplo: Toda librería expone su funcionalidad vía CLI; protocolo de texto entrada/salida: stdin/args → stdout, errores → stderr; soportar formatos JSON + legible por humanos -->

### [NOMBRE_PRINCIPIO_3]
<!-- Ejemplo: III. Test-First (NO NEGOCIABLE) -->
[DESCRIPCION_PRINCIPIO_3]
<!-- Ejemplo: TDD obligatorio: tests escritos → aprobados por el usuario → tests fallan → entonces se implementa; ciclo Rojo-Verde-Refactor aplicado estrictamente -->

### [NOMBRE_PRINCIPIO_4]
<!-- Ejemplo: IV. Testing de Integración -->
[DESCRIPCION_PRINCIPIO_4]
<!-- Ejemplo: Áreas que requieren tests de integración: tests de contrato de nuevas librerías, cambios de contrato, comunicación entre servicios, esquemas compartidos -->

### [NOMBRE_PRINCIPIO_5]
<!-- Ejemplo: V. Observabilidad, VI. Versionado y Cambios Incompatibles, VII. Simplicidad -->
[DESCRIPCION_PRINCIPIO_5]
<!-- Ejemplo: E/S de texto garantiza depurabilidad; se requiere logging estructurado; o: formato MAJOR.MINOR.BUILD; o: empezar simple, principios YAGNI -->

## [NOMBRE_SECCION_2]
<!-- Ejemplo: Restricciones Adicionales, Requisitos de Seguridad, Estándares de Rendimiento, etc. -->

[CONTENIDO_SECCION_2]
<!-- Ejemplo: requisitos de stack tecnológico, estándares de cumplimiento, políticas de despliegue, etc. -->

## [NOMBRE_SECCION_3]
<!-- Ejemplo: Flujo de Desarrollo, Proceso de Revisión, Quality Gates, etc. -->

[CONTENIDO_SECCION_3]
<!-- Ejemplo: requisitos de revisión de código, gates de testing, proceso de aprobación de despliegue, etc. -->

## Gobernanza
<!-- Ejemplo: la constitución prevalece sobre cualquier otra práctica; las enmiendas requieren documentación, aprobación, plan de migración -->

[REGLAS_GOBERNANZA]
<!-- Ejemplo: todo PR/revisión debe verificar cumplimiento; toda complejidad debe justificarse; usar [FICHERO_GUIA] para orientación de desarrollo en tiempo real -->

**Versión**: [VERSION_CONSTITUCION] | **Ratificada**: [FECHA_RATIFICACION] | **Última enmienda**: [FECHA_ULTIMA_ENMIENDA]
<!-- Ejemplo: Versión: 2.1.1 | Ratificada: 2025-06-13 | Última enmienda: 2025-07-16 -->
