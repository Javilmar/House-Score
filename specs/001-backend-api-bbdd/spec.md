# Especificación de Funcionalidad: Backend (API + Base de Datos) para HouseScore

**Rama de la funcionalidad**: `001-backend-api-bbdd`

**Creada**: 2026-09-08

**Estado**: Borrador

**Entrada**: Descripción del usuario: "Introducir un backend (API + base de datos) para HouseScore, sustituyendo el flujo actual de JSON commiteado en frontend/datos/. Cubrir: diseño de la base de datos para listings + histórico, una API que sirva esos datos ya puntuados, dockerización para pruebas locales reproducibles, decidir dónde se despliega en producción, y cualquier otra pieza necesaria. El front actual no se reescribe en este spec — seguirá desplegándose (previsiblemente en Vercel) y en un spec futuro pasará a consumir esta API en vez de leer JSON del repo."

## Clarifications

### Session 2026-09-08

- Q: ¿Los endpoints de lectura de la API deben ser completamente públicos sin autenticación, o con algún control mínimo como rate limiting? → A: Públicos, sin autenticación, con rate limiting básico por IP.
- Q: ¿La API debe exponer ya un endpoint de lectura para el histórico agregado (gráficos de evolución), o basta con guardarlo en la BBDD y añadir ese endpoint en un spec futuro? → A: Sí, incluir el endpoint de histórico ya en este spec.
- Q: ¿El sistema debe notificar activamente cuando el worker del scraper falla en guardar una pasada, o basta con que quede registrado en un log sin notificación activa? → A: Solo logging — los fallos quedan registrados y consultables, sin notificación activa.

## User Scenarios & Testing *(obligatorio)*

### Historia de Usuario 1 - El front deja de depender de ficheros commiteados (Prioridad: P1)

Como front de HouseScore (hoy el dashboard de Streamlit), quiero obtener los
listings de vivienda ya puntuados a través de una API en vez de leer ficheros
JSON del repositorio, para que la app en producción muestre siempre los datos
más recientes sin depender de un `git push` desde el ordenador del
propietario.

**Por qué esta prioridad**: es la razón de ser de este spec — es el cambio
que rompe la dependencia actual del front con los datos del repo (Principio
II de la constitución, Fase 2). Sin esto, el resto del backend no tiene
consumidor.

**Test independiente**: se puede verificar completamente pidiendo a la API
la lista de listings puntuados y comprobando que la respuesta contiene los
mismos campos y el mismo score que hoy calcula `property_scorer` sobre esos
listings, sin que el front necesite tocar `frontend/datos/`.

**Acceptance Scenarios**:

1. **Dado** que existen listings guardados en la base de datos, **Cuando**
   se solicitan a la API los listings de una zona, **Entonces** la respuesta
   incluye cada listing con su score ya calculado y su estado
   `datos_insuficientes` cuando aplique.
2. **Dado** que un listing no tiene m² fiables, **Cuando** se sirve desde la
   API, **Entonces** aparece marcado como `datos_insuficientes` y sin un
   score forzado, igual que hoy en el dashboard.

---

### Historia de Usuario 2 - Cada pasada del scraper queda disponible sin intervención manual (Prioridad: P1)

Como propietario del proyecto, quiero que el scraper corra como un worker
dentro de la misma infraestructura que la API (no en mi ordenador) y que
cada pasada quede reflejada en la base de datos llamando a un endpoint de
escritura de la API, para que publicar una nueva pasada no dependa de que mi
ordenador esté encendido ni de que se haga `git push` a este repositorio.

**Por qué esta prioridad**: es el otro lado del mismo cambio — si el front
lee de la API pero nadie escribe ahí, no hay progreso real. Junto con la
Historia 1 forman el MVP de este spec.

**Test independiente**: se puede testear ejecutando el flujo de guardado de
una pasada de ejemplo y comprobando que los listings aparecen disponibles
para la API inmediatamente después, sin ningún paso de git de por medio.

**Acceptance Scenarios**:

1. **Dado** un archivo de resultados de una pasada de scraping, **Cuando**
   el worker del scraper lo envía al endpoint de escritura de la API,
   **Entonces** los listings quedan persistidos y son consultables por la
   API sin necesidad de un commit a este repositorio.
2. **Dado** que un listing ya existente baja de precio en una nueva pasada,
   **Cuando** se guarda esa pasada, **Entonces** se conserva el precio
   anterior como historial de bajada de precio (equivalente al
   comportamiento actual de `guardar.py`).
3. **Dado** un listing de un municipio de Toledo Norte ya descartado (ver
   Principio V / lista de bloqueados actual), **Cuando** llega en una nueva
   pasada, **Entonces** se descarta antes de persistirse, igual que hoy.

---

### Historia de Usuario 3 - Entorno local reproducible para probar el backend (Prioridad: P2)

Como propietario del proyecto (que también hace de único desarrollador),
quiero poder levantar el backend completo (API + base de datos) en mi
ordenador con un único comando, para poder probar cambios antes de
desplegarlos, sin tener que instalar ni configurar manualmente una base de
datos en mi sistema.

**Por qué esta prioridad**: no bloquea el MVP funcional (Historias 1 y 2),
pero sin esto el desarrollo del backend viola el Principio IV de la
constitución (TDD): sin un entorno local reproducible, escribir y ejecutar
tests de forma fiable es mucho más costoso.

**Test independiente**: se puede testear clonando el repositorio en una
máquina limpia y comprobando que el backend queda operativo con un único
comando, sin pasos de configuración manual adicionales.

**Acceptance Scenarios**:

1. **Dado** un checkout limpio del repositorio, **Cuando** se ejecuta el
   comando de arranque local del backend, **Entonces** la API y la base de
   datos quedan operativas y listas para recibir peticiones sin
   configuración manual adicional.
2. **Dado** el entorno local en marcha, **Cuando** se ejecuta la suite de
   tests del backend, **Entonces** los tests corren contra ese entorno local
   sin tocar ningún dato de producción.

---

### Edge Cases

- ¿Qué ocurre si el worker del scraper pierde conexión a mitad de guardar
  una pasada (llamando al endpoint de escritura)? Los listings ya
  persistidos no deben quedar en un estado inconsistente ni duplicarse en un
  reintento.
- ¿Qué ocurre si la API recibe una petición de lectura mientras se está
  guardando una nueva pasada? Debe devolver siempre un conjunto de datos
  consistente (o la pasada anterior completa, o la nueva completa — nunca
  una mezcla a medias).
- ¿Cómo se refleja un listing que desaparece del scraping durante varios
  días (delisted), igual que hoy detecta `guardar.py` con el umbral de 7
  días?
- ¿Qué pasa si dos pasadas del scraper se ejecutan casi a la vez (p. ej. un
  reintento manual)? No deben crear listings duplicados.

## Requirements *(obligatorio)*

### Functional Requirements

- **FR-001**: El sistema DEBE exponer, vía API, los listings de vivienda
  vigentes junto con su score ya calculado por el motor de scoring existente
  (Principio I de la constitución: el motor de scoring no se reimplementa).
- **FR-002**: El sistema DEBE persistir los listings y su histórico diario
  en un almacén de datos duradero, sustituyendo a los ficheros
  `frontend/datos/*.json` como fuente de verdad.
- **FR-003**: El sistema DEBE permitir guardar una nueva pasada de resultados
  del scraper en el almacén de datos sin requerir un `git commit`/`git push`
  a este repositorio.
- **FR-004**: El sistema DEBE conservar, por cada listing, el historial de
  bajadas de precio (precio anterior → precio nuevo → fecha), igual que hoy
  hace `guardar.py`.
- **FR-005**: El sistema DEBE marcar como `datos_insuficientes` los listings
  sin m² fiables y excluirlos del cálculo de score medio, igual que hoy.
- **FR-006**: El sistema DEBE descartar antes de persistir los listings de
  municipios ya bloqueados (lista actual de Toledo Norte descartado en
  `guardar.py`).
- **FR-007**: El sistema DEBE detectar y marcar como retirados (delisted) los
  listings que llevan un número de días sin aparecer en ninguna pasada
  (mismo umbral que hoy: 7 días).
- **FR-008**: El sistema DEBE poder ejecutarse por completo (API + base de
  datos) en un entorno local aislado, reproducible con un único comando, sin
  afectar a ningún entorno de producción.
- **FR-009**: El sistema DEBE evitar crear listings duplicados cuando el
  mismo listing aparece en más de una pasada (identificado por su URL/id
  único, igual que hoy).
- **FR-010**: El sistema DEBE exponer un endpoint de escritura en la API para
  que el proceso de scraping guarde en él cada nueva pasada de resultados
  (en vez de escribir directamente en la base de datos).
- **FR-011**: El endpoint de escritura de la API NO DEBE ser accesible desde
  fuera de la red privada en la que corre el backend — no requiere
  autenticación adicional porque no existe ninguna ruta pública hacia él; el
  scraper corre como un worker dentro de esa misma red/infra, no desde el
  ordenador del propietario.
- **FR-012**: Los endpoints de lectura de la API (los que consulta el front)
  DEBEN quedar públicos y sin autenticación, igual que hoy los datos son
  públicos, pero DEBEN aplicar un límite de peticiones (rate limiting) básico
  por IP para evitar abuso del servicio.
- **FR-013**: El sistema DEBE exponer, vía API, el histórico agregado por día
  (equivalente a `historico_diario.json`), para que los gráficos de
  evolución que ya tiene el dashboard puedan seguir mostrándose cuando el
  front migre a consumir esta API.
- **FR-014**: El sistema DEBE registrar en un log consultable cualquier fallo
  del worker del scraper al guardar una pasada (p. ej. error al escribir en
  el endpoint de escritura o en la base de datos). No se requiere ningún
  mecanismo de notificación activa (email, push, etc.) en esta fase.

### Key Entities

- **Listing (piso)**: identificador único (p. ej. URL de origen), título,
  precio, m², habitaciones, baños, municipio/ubicación, fuente
  (pisos.com/idealista), score calculado, indicador `datos_insuficientes`,
  fecha de primera aparición, estado (activo/retirado).
- **Historial de precio**: listing al que pertenece, precio anterior, precio
  nuevo, fecha del cambio — permite reconstruir las bajadas de precio que
  hoy se muestran en el dashboard.
- **Pasada diaria (histórico agregado)**: fecha, métricas agregadas del día
  (equivalente a `historico_diario.json`) — alimenta los gráficos de
  evolución del dashboard.
- **Precio de referencia por municipio**: municipio, mediana €/m² (fuente:
  equivalente a `config/precios_referencia.json`), usado por el motor de
  scoring quando un listing no aporta m² fiables.

## Success Criteria *(obligatorio)*

### Measurable Outcomes

- **SC-001**: El front puede mostrar la lista completa de listings vigentes
  obteniéndolos únicamente de la API, sin leer ningún fichero JSON de este
  repositorio.
- **SC-002**: Una nueva pasada del scraper queda disponible para su consulta
  a través de la API en menos de 5 minutos desde que termina de guardarse,
  sin ningún paso manual de git.
- **SC-003**: El backend completo (API + base de datos) queda operativo en
  un entorno local limpio ejecutando un único comando, en menos de 5
  minutos, sin pasos de configuración manual adicionales.
- **SC-004**: El 100% del histórico de precios y pasadas existente en
  `frontend/datos/` sigue disponible y consultable tras la migración — cero
  pérdida de datos históricos.
- **SC-005**: Ningún listing aparece duplicado tras ejecutar la misma pasada
  del scraper dos veces seguidas.

## Assumptions

- El motor de scoring (`property_scorer` / `listings_store`) se reutiliza
  tal cual desde el backend; este spec no reimplementa ni cambia su lógica
  de puntuación (Principio I).
- El front consumidor de esta API sigue siendo, inicialmente, el dashboard
  actual — no se asume ningún otro cliente ni multiusuario en esta fase.
- Los datos de vivienda siguen siendo públicos, como fija la constitución en
  "Restricciones de Datos y Despliegue" — este spec no introduce
  restricciones de acceso salvo lo que resuelvan las clarificaciones
  pendientes sobre el canal de escritura.
- El scraper deja de ejecutarse en el ordenador local del propietario y pasa
  a correr como un worker dentro de la misma infraestructura que la API (así
  puede llamar a su endpoint de escritura sin exponerlo a internet, según lo
  resuelto en FR-010/FR-011). Este spec asume que ese worker existe y llama
  a la API, pero la implementación concreta de cómo se programa/despliega
  ese worker (cron, cola de tareas, contenedor propio...) se decide en
  `/speckit-plan`.
- La elección concreta de tecnología (lenguaje, framework, motor de base de
  datos, proveedor de hosting, y si se usa Docker) se decide en
  `/speckit-plan`, no en este spec — la constitución deja el stack de
  backend intencionadamente abierto.
- El corte del front de leer JSON del repo a consumir esta API es un spec
  futuro y no se implementa aquí (Principio VI: corte duro, no shims
  temporales); este spec entrega el backend, no la migración del front.
- Este spec no introduce usuarios ni un sistema de autenticación/autorización
  de usuarios — el único mecanismo de protección es el secreto compartido
  del endpoint de ingesta (ver `plan.md` / `research.md`). El propietario
  quiere usuarios reales en el futuro; cuando llegue ese momento, hará falta
  un spec propio de autenticación de usuarios que sustituya este mecanismo,
  no que lo amplíe de forma improvisada.
