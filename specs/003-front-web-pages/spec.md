# Especificación de Funcionalidad: Front web en la nube (Fase 3)

**Rama de la funcionalidad**: `003-front-web-pages`

**Creada**: 2026-10-21

**Estado**: Borrador

**Entrada**: Descripción del usuario: "Desplegar todo el proyecto en la nube y gratis: base de datos en Neon, API en Render y el front en Cloudflare Pages en lugar de Streamlit. Se elige el camino de la Fase 3 de la constitución (un front web que sustituye a Streamlit) en vez de llevar Streamlit al navegador con stlite."

## Clarifications

### Session 2026-10-21

- Q: ¿Dónde vive la base de datos? → A: En Neon (PostgreSQL gestionado, plan gratuito), rama `production`. Ya conectada en el commit `b6c7fd7`: la API usa la conexión con pooler y las migraciones la directa. Sustituye al PostgreSQL en Docker del PC del propietario de la spec 001.
- Q: ¿Dónde corre la API? → A: En Render (plan gratuito), desde el repositorio. Sustituye al Docker Compose local y al túnel `cloudflared` de la spec 001 (T050 deja de aplicar).
- Q: ¿Qué vistas deben estar antes del corte? → A: Las 8 actuales, sin excepción: Listados completos, Top scoring, Novedades, Evolución y análisis, Bajadas de precio, Hipoteca, Cómo funciona y Mapas.
- Q: ¿De dónde sale el histórico? → A: Del volcado `C:\Users\LWD12\Downloads\housescore-2026-10-21_1354.dump` que ha facilitado el propietario (pg_dump custom de la base de datos local, 2026-10-21 11:54 UTC).
- Q: ¿Dónde corre el front? → A: En Cloudflare Pages, sin dominio propio (dirección `*.pages.dev`). Es la Fase 3 de la constitución: un front web sustituye a Streamlit. Se descarta stlite (Streamlit en el navegador) por profundizar en una fase que el proyecto está dejando atrás (Principio II).
- Q: ¿Y el scorer? → A: Sigue en el PC del propietario (Playwright + sesión de idealista, inviable en un datacenter; spec 001, research §5) y pasa a enviar cada pasada a la API publicada en Render.
- Q: ¿Se mantiene la API despierta con un ping programado? → A: No. Se acepta el arranque en frío del plan gratuito; el front lo cubre con el estado de espera de FR-004. Sin pings programados.

## User Scenarios & Testing *(obligatorio)*

### Historia de Usuario 1 - Consultar los pisos desde cualquier sitio (Prioridad: P1)

Como propietario del proyecto, quiero abrir una dirección web desde el móvil o
cualquier ordenador, con mi PC apagado, y ver los listings actuales con su
score, filtros y desglose, para revisar pisos sin depender de tener el equipo
encendido ni de ejecutar nada en local.

**Por qué esta prioridad**: es el objetivo del cambio. Hoy el dashboard solo
existe en local y la API y la base de datos dependen del PC.

**Test independiente**: con el PC del propietario apagado, abrir la dirección
pública del front y comprobar que el nº de listings, el score medio y el
último día con pasada coinciden con lo que devuelve la API publicada.

**Acceptance Scenarios**:

1. **Dado** que la API publicada tiene listings, **Cuando** abro la dirección
   del front, **Entonces** veo los KPIs de cabecera (total, nuevos hoy, score
   medio, precio medio, bajadas, sin valorar) y la tabla de listados.
2. **Dado** la tabla de listados, **Cuando** combino filtros de zona,
   municipio, rango de score, rango de precio y habitaciones, **Entonces** el
   filtro de municipio se restringe a las zonas elegidas y la tabla y los
   totales reflejan solo los pisos que cumplen todos los filtros.
3. **Dado** un listing con desglose de score, **Cuando** lo despliego,
   **Entonces** veo los mismos bloques y puntos que el dashboard actual.
4. **Dado** un listing sin datos suficientes, **Cuando** se muestra,
   **Entonces** aparece "sin valorar" y sin score forzado (Principio I).
5. **Dado** listings retirados, **Cuando** activo "mostrar retirados",
   **Entonces** aparecen marcados como retirados; sin activarlo no cuentan.
6. **Dado** un título de listing, **Cuando** lo pulso, **Entonces** se abre el
   anuncio original en una pestaña nueva.

---

### Historia de Usuario 2 - Aviso claro cuando la API está dormida o caída (Prioridad: P1)

Como propietario del proyecto, quiero que, si la API tarda en despertar o no
responde, el front me lo diga claramente y se recupere solo, para no ver una
pantalla rota ni datos viejos sin saberlo.

**Por qué esta prioridad**: en el plan gratuito la API se suspende tras un
rato sin uso y la primera visita puede tardar del orden de un minuto en
responder. Sin este comportamiento, la primera visita del día parecería un
fallo.

**Test independiente**: con la API suspendida, abrir el front y comprobar que
muestra un estado de "despertando el servidor" y que, al responder la API,
carga los datos sin recargar a mano; con la API caída de verdad, comprobar que
acaba mostrando el aviso de error con la dirección consultada y ninguna cifra.

**Acceptance Scenarios**:

1. **Dado** que la API está suspendida, **Cuando** abro el front, **Entonces**
   veo un indicador de espera que explica que el servidor está arrancando, y
   los datos aparecen cuando responde.
2. **Dado** que la API no responde tras el tiempo máximo de espera, **Cuando**
   se agota, **Entonces** veo un aviso con qué ha fallado y la dirección
   consultada, sin cifras ni tablas, y un botón para reintentar.
3. **Dado** que la API responde sin listings, **Cuando** abro el front,
   **Entonces** veo "sin datos", distinto del aviso de API no disponible.
4. **Dado** que la API rechaza por límite de peticiones, **Cuando** ocurre,
   **Entonces** veo un aviso claro y el front no reintenta en bucle.

---

### Historia de Usuario 3 - El scorer publica en la nube (Prioridad: P1)

Como propietario del proyecto, quiero que el job diario del scorer en mi PC
envíe cada pasada a la API publicada, para que el front muestre los datos
del día sin ningún paso manual.

**Por qué esta prioridad**: sin escritor, el front publicado se queda con
datos parados.

**Test independiente**: forzar una pasada del scorer y comprobar que el front
publicado muestra la fecha y los listings de esa pasada al recargar.

**Acceptance Scenarios**:

1. **Dado** que el job diario se ejecuta, **Cuando** termina un lote,
   **Entonces** su pasada queda guardada en la base de datos en la nube y se
   ve en el front al recargar.
2. **Dado** que la API está suspendida al empezar el job, **Cuando** el scorer
   la comprueba, **Entonces** espera a que despierte en lugar de abortar el
   lote.
3. **Dado** una petición de escritura sin el secreto correcto, **Cuando** llega
   a la API publicada, **Entonces** se rechaza y no se escribe nada.

---

### Historia de Usuario 4 - El histórico existente no se pierde (Prioridad: P1)

Como propietario del proyecto, quiero que los listings, el historial de
precios y las pasadas diarias acumulados hasta hoy estén en la base de datos
en la nube, para que la evolución y las bajadas de precio sigan teniendo
sentido tras el cambio.

**Por qué esta prioridad**: la base de datos en la nube está hoy vacía; sin
el histórico se pierden la evolución diaria y la detección de bajadas.

**Test independiente**: comparar recuentos de listings, historial de precios y
pasadas diarias entre el origen y la base de datos en la nube tras migrar.

**Acceptance Scenarios**:

1. **Dado** el volcado `housescore-2026-10-21_1354.dump` (formato custom de `pg_dump`, PostgreSQL 16.14, creado el 2026-10-21 11:54 UTC, con las 5 tablas), **Cuando** se restaura en la base de datos en la nube, **Entonces** los recuentos de cada tabla coinciden con el volcado.
2. **Dado** que entre el volcado y el cambio del scorer a la nube puede haber pasadas nuevas en la base de datos local, **Cuando** se migra, **Entonces** se usa un volcado posterior a la última pasada local, o se acepta y documenta la pérdida de esas pasadas.

---

### Historia de Usuario 5 - Las mismas vistas que hoy (Prioridad: P2)

Como propietario del proyecto, quiero en el front web las mismas vistas que
el dashboard actual, para no perder herramientas al dejar Streamlit.

**Por qué esta prioridad**: el corte es duro (Principio VI): al publicar el
front se retira Streamlit, así que lo que no esté en el front deja de existir.

**Test independiente**: recorrer cada vista de la lista y comprobar que
existe y funciona con los datos de la API.

**Acceptance Scenarios**:

1. **Dado** el front publicado, **Cuando** lo recorro, **Entonces** encuentro
   las 8 vistas actuales: Listados completos, Top scoring, Novedades,
   Evolución y análisis, Bajadas de precio, Hipoteca (con gastos mensuales
   estimados), Cómo funciona y Mapas (criminalidad por municipio y renta por
   sección censal), cada una con el mismo contenido que hoy.
2. **Dado** un listing en Listados, Top scoring o Bajadas, **Cuando** pulso su
   botón de hipoteca, **Entonces** la calculadora se abre precargada con su
   precio, tipo de vivienda y comunidad autónoma.
3. **Dado** los listings filtrados, **Cuando** pulso "Descargar CSV",
   **Entonces** descargo exactamente los listings visibles.

---

### Edge Cases

- ¿Qué ocurre si la API publicada tarda más que el tiempo máximo de espera
  pero luego despierta? El botón de reintentar debe cargar los datos sin
  recargar la página entera.
- ¿Qué ocurre si la base de datos en la nube también está suspendida? La
  primera consulta tarda algo más; no debe tratarse como error.
- ¿Qué ocurre si alguien desde otro sitio web intenta leer la API? Solo el
  origen del front publicado (y el local de desarrollo) puede leerla desde un
  navegador.
- ¿Qué ocurre con el volumen? Unos 2.000 listings (activos y retirados): el
  front debe filtrar y ordenar sin esperas perceptibles.
- ¿Qué ocurre en el móvil? Las vistas deben poder usarse en pantalla estrecha
  (tabla con desplazamiento horizontal, filtros plegables).
- ¿Qué ocurre si la API devuelve un campo opcional ausente (sin
  `score_details`, sin descripción)? Se muestra vacío u omitido, sin romper.
- ¿Qué ocurre con los recursos del mapa (geometrías de ~3 MB)? Se sirven como
  ficheros estáticos del front y solo se descargan al abrir la vista de mapas.

## Requirements *(obligatorio)*

### Functional Requirements

- **FR-001**: El front DEBE ser accesible públicamente en una dirección fija,
  sin dominio propio, y funcionar con el PC del propietario apagado.
- **FR-002**: El front DEBE obtener listings (activos y retirados) e histórico
  exclusivamente de la API publicada, cuya dirección se fija al construir el
  front, sin leer datos de ficheros del repositorio.
- **FR-003**: El front DEBE mostrar los KPIs de cabecera, la tabla de
  listados con filtros combinativos y ordenación por columna, el desglose de
  score, la marca "sin valorar", la marca de retirado y el enlace al anuncio,
  con el mismo significado que el dashboard actual.
- **FR-004**: El front DEBE mostrar un estado de espera mientras la API
  despierta, con un tiempo máximo de espera de al menos 90 segundos, y tras
  agotarlo un aviso con el problema, la dirección consultada y un botón de
  reintentar, sin cifras de datos.
- **FR-005**: El front DEBE distinguir "API no disponible", "límite de
  peticiones" y "API sin listings", y NO DEBE reintentar en bucle.
- **FR-006**: La API DEBE aceptar lecturas desde navegador solo desde el
  origen del front publicado y del entorno local de desarrollo, y solo para
  las rutas de lectura.
- **FR-007**: La ruta de escritura de la API queda expuesta a internet y DEBE
  rechazar toda petición sin el secreto compartido correcto (sustituye a
  FR-011 de la spec 001, que la dejaba fuera del túnel).
- **FR-008**: El scorer DEBE publicar en la API en la nube y DEBE tolerar que
  esté suspendida al empezar, esperando a que responda dentro de un límite.
- **FR-009**: El histórico existente DEBE migrarse a la base de datos en la
  nube con recuentos verificables por tabla.
- **FR-010**: El front DEBE incluir las vistas acordadas en la Historia 5,
  con la navegación precargada a la calculadora de hipoteca y la descarga CSV
  de los listings filtrados.
- **FR-011**: El front DEBE respetar la identidad visual actual: modo oscuro
  siempre, un único color de acento (`#6366f1`), escala de color de score
  actual, iconos SVG en vez de emojis.
- **FR-012**: Al publicar el front se DEBE retirar el dashboard de Streamlit
  (`frontend/dashboard/app.py`, `api_datos.py` y sus dependencias), sin modo
  de compatibilidad (Principio VI), y actualizar la documentación que lo
  describe.
- **FR-013**: Las credenciales (cadena de conexión, secreto de escritura) NO
  DEBEN commitearse: viven en el gestor de secretos de cada plataforma.
- **FR-014**: El comportamiento del front (filtros, cálculos de KPIs,
  calculadora de hipoteca, estados de error) DEBE estar cubierto por tests
  escritos antes que la implementación (Principio IV).

### Key Entities

- **Listing (piso)**: el que sirve la API de la spec 001 (título, precio, m²,
  habitaciones, baños, municipio, fuente, score, datos insuficientes, estado
  activo/retirado, primera y última aparición, bajada de precio) más su
  detalle (desglose de score, descripción, €/m², características).
- **Pasada diaria**: fecha, nº de listings, score medio, precio medio, mínimo
  y máximo.
- **Recursos del mapa**: geometrías municipales, criminalidad por municipio y
  renta por sección censal; estáticos, sin cambios de contenido.

## Success Criteria *(obligatorio)*

### Measurable Outcomes

- **SC-001**: Con el PC del propietario apagado, el front publicado muestra
  los datos de la última pasada.
- **SC-002**: Con la API ya despierta, la primera pantalla con datos aparece
  en menos de 3 segundos en una conexión doméstica.
- **SC-003**: Con la API suspendida, el 100% de las aperturas acaban en datos
  o en el aviso de error, nunca en una pantalla en blanco ni en un error
  técnico sin explicar.
- **SC-004**: Tras una pasada del scorer, el front la refleja al recargar, sin
  ningún paso manual.
- **SC-005**: Los recuentos de listings, historial de precios y pasadas
  diarias en la nube coinciden con el origen tras la migración.
- **SC-006**: Filtrar u ordenar ~2.000 listings responde en menos de 200 ms.
- **SC-007**: No queda en el repositorio código del dashboard de Streamlit
  ni documentación que indique ejecutarlo.
- **SC-008**: Coste mensual de la infraestructura: 0 €.

## Assumptions

- Contrato de la API sin cambios de forma: `GET /listings?incluir_retirados=true`,
  `GET /historico` y `POST /ingest` como en la spec 001. Solo se añaden
  permisos de origen para navegador y ajustes de despliegue.
- Un único usuario; los datos de vivienda pueden ser públicos (constitución,
  "Visibilidad de los datos"), así que el front no lleva autenticación.
- El cálculo del score sigue en el scorer (Principio I); el front solo muestra
  el score y su desglose, nunca lo recalcula.
- La calculadora de hipoteca y los gastos mensuales son cálculos de
  presentación, no de scoring, y se reimplementan en el front con los mismos
  tipos fiscales que hoy.
- Plataformas gratuitas con sus límites: la API se suspende tras inactividad;
  la base de datos se suspende tras unos minutos sin uso.
- `frontend/config/precios_referencia.json` lo usa el scorer, no el
  dashboard, y no cambia.
- La constitución nombra Vercel como ejemplo de plataforma de la Fase 3 y
  Streamlit Community Cloud como objetivo de despliegue actual; este spec
  aplica la Fase 3 con Cloudflare Pages, y su cierre debe actualizar la
  sección "Restricciones de Datos y Despliegue" vía `/speckit-constitution`.
