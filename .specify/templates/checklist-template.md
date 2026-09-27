# Checklist de [TIPO DE CHECKLIST]: [NOMBRE DE LA FUNCIONALIDAD]

**Propósito**: [Breve descripción de qué cubre esta checklist]
**Creada**: [FECHA]
**Funcionalidad**: [Enlace a spec.md o documentación relevante]

**Nota**: Esta checklist a medida la genera el comando `/speckit-checklist` según el contexto y los requisitos de la funcionalidad.
**Propiedad de la revisión**: Esta checklist es un artefacto de revisión de calidad de requisitos, propiedad de quien revisa. Marca un ítem `[x]` solo cuando quien revisa determine que el criterio de calidad de requisitos se cumple.
**Semántica de la marca**: `[x]` significa que el criterio se ha revisado y se cumple en cuanto a calidad de requisitos. No significa que el trabajo de implementación esté completo.

<!--
  ============================================================================
  IMPORTANTE: Los ítems de la checklist de abajo son ÍTEMS DE EJEMPLO solo a
  modo ilustrativo.

  El comando /speckit-checklist DEBE sustituirlos por ítems reales basados en:
  - La petición de checklist concreta del usuario
  - Los requisitos de la funcionalidad en spec.md
  - El contexto técnico de plan.md
  - Los detalles de implementación de tasks.md

  NO dejes estos ítems de ejemplo en el fichero de checklist generado.
  ============================================================================
-->

## [Categoría 1]

- [ ] CHK001 Primer ítem de la checklist con una acción clara
- [ ] CHK002 Segundo ítem de la checklist
- [ ] CHK003 Tercer ítem de la checklist

## [Categoría 2]

- [ ] CHK004 Otro ítem de categoría
- [ ] CHK005 Ítem con criterios específicos
- [ ] CHK006 Último ítem de esta categoría

## Notas

- Marca los ítems `[x]` solo tras confirmar en la revisión que se cumple el criterio de calidad de requisitos
- Deja los ítems sin marcar mientras necesiten aclaración, corrección o evaluación de quien revisa
- `/speckit-implement` lee el estado de las casillas de la checklist como gate y no debe modificar las marcas
- `checklists/requirements.md` tiene un ciclo de vida propio, mantenido por `/speckit-specify` y `/speckit-clarify`
- Añade comentarios o hallazgos en línea
- Enlaza a recursos o documentación relevante
- Los ítems están numerados secuencialmente para facilitar su referencia
