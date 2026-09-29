# Especificación de Funcionalidad: El dashboard consume la API

**Rama de la funcionalidad**: `002-front-consume-api`

**Creada**: 2026-09-29

**Estado**: Borrador

**Entrada**: Descripción del usuario: "El dashboard de Streamlit (frontend/dashboard/app.py) pasa de leer frontend/datos/listings.json y historico_diario.json a ser cliente de la API del backend (GET /listings?incluir_retirados=true y GET /historico, en http://localhost:8000 configurable por variable de entorno). Debe mostrar exactamente lo mismo que hoy (tablas, KPIs, gráficos, desglose de score, precios de referencia) sin tocar el resto de la app, usando el campo detalle de la API para score_details, description, eur_m2, etc. Corte duro sin shims: se retira la lectura de los JSON del repo. Si la API no responde debe mostrar un aviso claro en lugar de datos viejos. Se ejecuta en local con streamlit run; el despliegue en la nube queda fuera de este spec (depende del túnel)."

## User Scenarios & Testing *(obligatorio)*

### Historia de Usuario 1 - El dashboard muestra los datos vivos de la API (Prioridad: P1)

Como propietario del proyecto, quiero abrir el dashboard y ver los mismos
listings, KPIs, tablas, gráficos y desglose de score que hoy, pero con los
datos actuales del backend, para dejar de depender de ficheros JSON
commiteados en el repositorio (que llevan parados desde el 2026-09-08).

**Por qué esta prioridad**: es la Fase 2 de la constitución (Principio II):
"el front de Streamlit pasa de leer ficheros commiteados a ser cliente de la
API". Sin esto, el backend ya en marcha no tiene consumidor y el dashboard
muestra datos obsoletos.

**Test independiente**: con la API en marcha y datos migrados, abrir el
dashboard y comprobar que el nº de listings, el score medio y el histórico
coinciden con lo que devuelve la API en ese momento, sin que exista ni se lea
ningún fichero de `frontend/datos/`.

**Acceptance Scenarios**:

1. **Dado** que la API tiene listings activos y retirados, **Cuando** abro el
   dashboard, **Entonces** veo las mismas pestañas, KPIs, tablas, filtros y
   gráficos que hoy, calculados sobre los datos que sirve la API.
2. **Dado** un listing con desglose de score, descripción y demás campos de
   detalle, **Cuando** lo consulto en el dashboard, **Entonces** veo el mismo
   desglose de score, descripción, €/m² y características que hoy.
3. **Dado** un listing retirado, **Cuando** activo "mostrar retirados",
   **Entonces** aparece marcado como retirado igual que hoy, y sin activarlo
   no aparece en las cifras de listings activos.
4. **Dado** un listing sin datos suficientes, **Cuando** se muestra,
   **Entonces** aparece "sin valorar", sin un score forzado (Principio I).
5. **Dado** que el backend recibe una pasada nueva del scraper, **Cuando**
   recargo el dashboard, **Entonces** veo la pasada nueva sin ningún paso de
   git ni de copia de ficheros.

---

### Historia de Usuario 2 - Aviso claro si la API no responde (Prioridad: P1)

Como propietario del proyecto, quiero que, si la API está caída o no
responde, el dashboard me lo diga de forma clara en lugar de mostrarme datos
viejos o una pantalla rota, para no tomar decisiones sobre información
obsoleta sin saberlo.

**Por qué esta prioridad**: hoy el dashboard ya muestra datos parados desde
septiembre sin avisar. Con la API como única fuente, "sin datos" debe ser
visible y explícito, no silencioso.

**Test independiente**: parar la API, abrir el dashboard y comprobar que
muestra un aviso comprensible con la dirección consultada, sin tablas ni
cifras de datos antiguos; volver a arrancar la API y comprobar que se
recupera al recargar.

**Acceptance Scenarios**:

1. **Dado** que la API no responde, **Cuando** abro el dashboard, **Entonces**
   veo un aviso claro (qué ha fallado y qué dirección se ha consultado) y
   ninguna cifra ni tabla de datos.
2. **Dado** que la API responde con un error o con datos ilegibles, **Cuando**
   abro el dashboard, **Entonces** veo el mismo tipo de aviso, no un error
   técnico sin explicar.
3. **Dado** que la API vuelve a estar disponible, **Cuando** recargo el
   dashboard, **Entonces** se recupera sin reiniciarlo.
4. **Dado** que la API responde pero sin listings, **Cuando** abro el
   dashboard, **Entonces** veo un mensaje de "sin datos" distinto del de
   "API no disponible".

---

### Historia de Usuario 3 - Configurar dónde está la API (Prioridad: P2)

Como propietario del proyecto, quiero indicar la dirección de la API mediante
una variable de entorno, con un valor por defecto que funcione en local, para
poder apuntar el dashboard a otra instancia más adelante (por ejemplo la
publicada por el túnel) sin tocar código.

**Por qué esta prioridad**: el uso inmediato es local (valor por defecto); la
configurabilidad prepara el despliegue en la nube, que queda fuera de este
spec.

**Test independiente**: arrancar el dashboard sin variable y comprobar que
consulta la dirección local por defecto; arrancarlo con la variable apuntando
a otra dirección y comprobar que consulta esa.

**Acceptance Scenarios**:

1. **Dado** que no hay variable de entorno definida, **Cuando** arranco el
   dashboard, **Entonces** consulta la API en la dirección local por defecto
   (`http://localhost:8000`).
2. **Dado** que defino la variable con otra dirección, **Cuando** arranco el
   dashboard, **Entonces** consulta esa dirección y el aviso de fallo (si lo
   hay) la menciona.

---

### Edge Cases

- ¿Qué ocurre si la API tarda mucho en responder? El dashboard debe dejar de
  esperar pasado un tiempo razonable y mostrar el aviso de la Historia 2, sin
  quedarse colgado.
- ¿Qué ocurre si el rate limiting de la API devuelve "demasiadas peticiones"?
  El dashboard debe mostrar un aviso claro y no reintentar en bucle.
- ¿Qué ocurre si la API devuelve un campo nuevo o le falta uno opcional del
  detalle (p. ej. sin `score_details`)? La pantalla no debe romperse: el campo
  ausente se muestra vacío o se omite, como hoy con los datos incompletos.
- ¿Qué ocurre con el volumen? La API sirve hoy unos 2.000 listings (activos y
  retirados); el dashboard debe seguir siendo fluido con esa cantidad.
- ¿Qué pasa con las instrucciones del propio dashboard que hoy explican cómo
  ejecutar el scorer y `guardar.py`? Deben reflejar el flujo nuevo o retirarse,
  no seguir indicando un flujo que ya no alimenta al dashboard.

## Requirements *(obligatorio)*

### Functional Requirements

- **FR-001**: El dashboard DEBE obtener los listings (activos y retirados) y el
  histórico diario exclusivamente de la API del backend, sin leer
  `frontend/datos/listings.json` ni `historico_diario.json`.
- **FR-002**: El dashboard DEBE mostrar las mismas pestañas, KPIs, filtros,
  tablas, gráficos y desgloses de score que hoy, sin cambios de
  comportamiento visibles para el usuario, salvo el origen de los datos.
- **FR-003**: El dashboard DEBE presentar cada listing con los mismos campos
  que hoy, incluidos el desglose de score, la descripción, el €/m², las
  características y las marcas de bajada de precio, a partir de lo que sirve
  la API.
- **FR-004**: El dashboard DEBE distinguir listings activos y retirados igual
  que hoy, y DEBE mostrar los que no tienen datos suficientes como "sin
  valorar", sin un score forzado (Principio I).
- **FR-005**: Si la API no responde, tarda demasiado, devuelve un error o
  devuelve datos ilegibles, el dashboard DEBE mostrar un aviso claro que
  indique el problema y la dirección consultada, y NO DEBE mostrar cifras ni
  tablas de datos antiguos.
- **FR-006**: El dashboard DEBE distinguir "la API no está disponible" de "la
  API no tiene listings".
- **FR-007**: El dashboard DEBE recuperarse sin reiniciarse cuando la API
  vuelve a estar disponible.
- **FR-008**: La dirección de la API DEBE poder configurarse mediante una
  variable de entorno, con `http://localhost:8000` como valor por defecto.
- **FR-009**: Se DEBE retirar del dashboard el código de lectura de los JSON
  del repositorio, sin dejar un modo de compatibilidad ni una alternativa por
  ficheros (Principio VI: corte duro sin shims).
- **FR-010**: El dashboard NO DEBE requerir credenciales para leer de la API:
  los endpoints de lectura son públicos (FR-012 de la spec 001).
- **FR-011**: Los textos del dashboard que describen el origen de los datos o
  el flujo de actualización (p. ej. "Datos en …", instrucciones del scorer y
  `guardar.py`) DEBEN reflejar el flujo nuevo o retirarse.
- **FR-012**: La carga de datos DEBE tener un tiempo máximo de espera y NO
  DEBE repetir peticiones en bucle si la API rechaza por límite de peticiones.

### Key Entities

- **Listing (piso)**: el mismo que sirve la API de la spec 001 (identificador,
  título, precio, m², habitaciones, baños, municipio, fuente, score, indicador
  de datos insuficientes, estado activo/retirado, primera y última aparición,
  marca de bajada de precio) más su detalle (desglose de score, descripción,
  €/m², características).
- **Pasada diaria (histórico agregado)**: fecha, nº de listings activos,
  score medio, precio medio, mínimo y máximo; alimenta el gráfico de
  evolución.

## Success Criteria *(obligatorio)*

### Measurable Outcomes

- **SC-001**: Abrir el dashboard con la API en marcha muestra los datos del
  último día con pasada (hoy: 2026-09-29), no los del 2026-09-08.
- **SC-002**: Ninguna de las pestañas que hoy funcionan deja de funcionar: el
  100% de las vistas actuales se muestran con datos de la API.
- **SC-003**: Con la API parada, el 100% de las aperturas del dashboard
  muestran el aviso y ninguna cifra de datos antiguos.
- **SC-004**: El dashboard carga y responde con ~2.000 listings sin esperas
  perceptibles (la primera pantalla aparece en menos de 5 segundos).
- **SC-005**: Tras una pasada nueva del scraper, el dashboard la refleja al
  recargar, sin ningún paso manual de git ni de copia de ficheros.
- **SC-006**: No queda en el dashboard ninguna lectura de `frontend/datos/*.json`.

## Assumptions

- El backend de la spec 001 está en marcha en local (`docker compose up`) y
  con los datos migrados; este spec no cambia la API (contrato ya definido:
  `GET /listings?incluir_retirados=true` y `GET /historico`).
- Uso local: el dashboard y la API corren en el mismo equipo. El despliegue del
  dashboard en la nube (Streamlit Community Cloud) queda fuera de este spec:
  depende del túnel `cloudflared` (T050 de la spec 001) y de decidir el hosting.
- El dashboard hoy solo lee `listings.json` e `historico_diario.json` de
  `frontend/datos/`; no lee `config/precios_referencia.json` (lo usa el
  scorer), por lo que los precios de referencia no forman parte de este cambio.
  Los recursos estáticos del propio dashboard (p. ej. el mapa de municipios en
  `assets/`) no cambian.
- Los nombres de campo del dashboard actual (`title`, `price`, `rooms`, ...)
  se conservan hacia el resto de la app; la traducción desde el contrato de la
  API ocurre en un único punto de carga, para no tocar el resto de la app.
- Retirar `guardar.py`, `listings_store.py` y `frontend/datos/` es parte de la
  tarea T052 de la spec 001 y no de este spec, salvo lo que este cambio deje
  sin uso dentro del propio dashboard.
- El dashboard es de un único usuario; no se introduce autenticación, ni
  cachés persistentes, ni escritura hacia la API: solo lectura.
- La frescura de los datos es la de la recarga del dashboard (hoy caché corta
  de 30 s); no se exige actualización en tiempo real.
