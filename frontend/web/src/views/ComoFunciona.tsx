/** Pestaña «Cómo funciona» (app.py `with tab7:`, 2148-2346). */
import type { ReactNode } from 'react'
import '../styles/expander.css'
import '../styles/como-funciona.css'

const POS = '#22c55e' // suma
const NEG = '#f87171' // resta
const NEU = '#818cf8' // base

type Fila = [concepto: string, pts: string, color: string]

function Bloque({ titulo, subtitulo, items }: { titulo: string; subtitulo: string; items: Fila[] }) {
  return (
    <div className="prop-card cf-bloque">
      <div className="cf-titulo">{titulo}</div>
      <div className="cf-sub">{subtitulo}</div>
      {items.map(([concepto, pts, color]) => (
        <div className="cf-fila" key={concepto}>
          <span className="cf-concepto">{concepto}</span>
          <span className="cf-pts" style={{ color }}>
            {pts}
          </span>
        </div>
      ))}
    </div>
  )
}

function Desplegable({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <details className="expander">
      <summary>{titulo}</summary>
      <div className="expander-body">{children}</div>
    </details>
  )
}

export default function ComoFunciona() {
  return (
    <div>
      <h2 className="sr-only-vista">Cómo funciona</h2>
      <p className="cf-intro">
        Cada anuncio recibe una <strong>puntuación de 0 a 100</strong>. Lo que más pesa es si está{' '}
        <strong>barato para su zona</strong>: su precio por m² comparado con la{' '}
        <strong>media de su municipio</strong>. A eso se suman tamaño, características (con tope), señales de
        mercado y penalizaciones. Cuanto más alta la nota, mejor oportunidad. Así se reparten los puntos:
      </p>

      <div className="cf-cols">
        <div className="cf-col">
          <Bloque
            titulo="💎 Valor vs zona"
            subtitulo="€/m² frente a la media de su municipio"
            items={[
              ['≈ 20% o más bajo la media (chollo)', '+25', POS],
              ['En la media de su zona', '≈ +12', NEU],
              ['≈ 20% o más por encima (caro)', '+0', NEG],
              ['Sin m² fiable → no se puede valorar', 'fuera del Top', NEG],
            ]}
          />
          <Bloque
            titulo="📐 Superficie"
            subtitulo="Cuanto más grande, mejor"
            items={[
              ['< 70 m² → no cumple requisitos', '—', NEG],
              ['≥ 140 m²', '+15', NEU],
              ['≥ 120 m²', '+12', NEU],
              ['≥ 100 m²', '+8', NEU],
              ['≥ 80 m²', '+5', NEU],
              ['≥ 70 m²', '+3', NEU],
              ['🛏️ 3 o más habitaciones', '+5', POS],
              ['🛏️ 2 habitaciones', '+2', POS],
              ['🛏️ 1 habitación → no cumple requisitos', '—', NEG],
            ]}
          />
          <Bloque
            titulo="📈 Señales de mercado"
            subtitulo="Cómo se comporta el anuncio en el tiempo"
            items={[
              ['📉 Ha bajado de precio', '+1 a +5', POS],
              ['🕸️ Lleva > 45 días anunciado', '−3', NEG],
              ['🕸️ Lleva > 90 días anunciado', '−5', NEG],
            ]}
          />
        </div>
        <div className="cf-col">
          <Bloque
            titulo="✨ Características"
            subtitulo="Detectadas en anuncio y ficha · el total se limita a +18"
            items={[
              ['🏊 Piscina', '+8', POS],
              ['🚗 Garaje', '+10', POS],
              ['📦 Trastero', '+6', POS],
              ['🛗 Ascensor', '+5', POS],
              ['Tope del bloque (no se acumula sin fin)', 'máx +18', NEU],
            ]}
          />
          <Bloque
            titulo="🌿 Exterior"
            subtitulo="Terraza, patio, jardín o balcón"
            items={[
              ['Detectado en anuncio o ficha', '+12', POS],
              ['Ficha leída y sin exterior', '−25', NEG],
              ['Ficha aún no leída', '0', NEU],
            ]}
          />
          <Bloque
            titulo="➕ Extras (suman)"
            subtitulo="Antigüedad, ubicación y calidad"
            items={[
              ['🏗️ Obra nueva / a estrenar', '+10', POS],
              ['🚇 Cerca de transporte público', '+8', POS],
              ['🔧 Reformado (si no es obra nueva)', '+5', POS],
              ['📅 Construido desde 2000', '+1 a +5', POS],
              ['🏢 Ático / última planta', '+3', POS],
              ['⚡ Eficiencia energética A/B/C', '+2', POS],
            ]}
          />
          <Bloque
            titulo="⚠️ Penalizaciones (restan)"
            subtitulo="Avisan de posibles problemas"
            items={[
              ['📍 Zona conflictiva', '−3 a −20', NEG],
            ]}
          />
        </div>
      </div>

      <h5 className="cf-seccion">De dónde salen los datos</h5>

      <Desplegable titulo="¿De qué portales vienen los anuncios?">
        <p>
          Los datos proceden de <strong>pisos.com</strong> (las 5 zonas) y{' '}
          <strong>fotocasa</strong> (las 4 zonas de Madrid, no Toledo Norte; si su anti-robot bloquea la pasada, esa búsqueda se omite
          sin interrumpir pisos.com). Cada anuncio lleva el campo <strong>Source</strong> indicando su
          origen.
        </p>
      </Desplegable>
      <Desplegable titulo="¿Qué municipios se rastrean?">
        <p>
          Nos centramos en municipios a <strong>30–40 min de Madrid por autovía</strong> (corredores A-42, A-4 y
          A-5). <strong>Toledo capital queda fuera</strong>: está a ~55 min y es un mercado distinto.
        </p>
        <div className="cf-municipios">
          <div>
            <p>
              <strong>Madrid Sur (18) · hasta 300.000 €</strong>
            </p>
            <p>
              Alcorcón · Arroyomolinos · Batres · Ciempozuelos · Cubas de la Sagra · Fuenlabrada · Getafe ·
              Griñón · Humanes de Madrid · Leganés · Móstoles · Moraleja de Enmedio · Navalcarnero · Parla ·
              Pinto · Serranillos del Valle · Torrejón de la Calzada · Valdemoro
            </p>
          </div>
          <div>
            <p>
              <strong>Madrid Este (6) · hasta 350.000 €</strong>
            </p>
            <p>
              Alcalá de Henares · Coslada · Mejorada del Campo · San Fernando de Henares · Torrejón de Ardoz ·
              Velilla de San Antonio
            </p>
          </div>
          <div>
            <p>
              <strong>Madrid Sureste (5) · hasta 300.000 €</strong>
            </p>
            <p>Arganda del Rey · Campo Real · Morata de Tajuña · Rivas-Vaciamadrid · San Martín de la Vega</p>
          </div>
          <div>
            <p>
              <strong>Madrid Norte (6) · hasta 400.000 €</strong>
            </p>
            <p>
              Alcobendas · Algete · Colmenar Viejo · San Agustín del Guadalix · San Sebastián de los Reyes · Tres
              Cantos
            </p>
          </div>
          <div>
            <p>
              <strong>Toledo Norte (5) · hasta 300.000 €</strong>
            </p>
            <p>Esquivias · Illescas · Seseña · Ugena · Yeles</p>
          </div>
        </div>
      </Desplegable>
      <Desplegable titulo="¿Cómo se asegura que el precio es real?">
        <p>
          El listado de búsqueda a veces muestra precios "desde", que engañan. Por eso el sistema puntúa primero
          todos los anuncios, <strong>visita la ficha completa de los mejores</strong> y vuelve a puntuarlos con
          los datos reales: precio, metros, habitaciones, baños, año y estado de conservación. Por eso algún
          anuncio puede aparecer algo por encima del tope de su zona: su precio real (de la ficha) subió respecto al del
          listado, pero si su €/m² es bueno se mantiene como oportunidad.
        </p>
      </Desplegable>
      <Desplegable titulo='¿Qué significa "barato para su zona"?'>
        <p>
          Es el factor que más pesa. Cada pasada calcula la <strong>mediana de €/m² de cada municipio</strong> a
          partir de todos los anuncios recogidos, y compara el €/m² de cada vivienda con esa media: si está por
          debajo, es un chollo y sube; si está por encima, baja. Si un municipio tiene pocos anuncios, se usa la
          media de su <strong>zona</strong> (Madrid Sur, Este, Sureste, Norte o Toledo Norte).{' '}
          <strong>Matiz</strong>: la media se calcula sobre anuncios de hasta el precio máximo de cada zona
          (300.000–400.000 €), así que es la referencia del <em>segmento asequible</em>, no
          del mercado completo.
        </p>
      </Desplegable>
      <Desplegable titulo='¿Por qué algunos salen como "sin valorar"?'>
        <p>
          Si un anuncio no trae los <strong>m² de forma fiable</strong> (faltan o el dato es absurdo), no se puede
          calcular su €/m² ni compararlo con su zona. Esos anuncios se marcan <strong>"s/valorar"</strong>, quedan{' '}
          <strong>fuera del Top</strong> y no cuentan en el "Score medio", pero siguen guardados por si quieres
          revisarlos.
        </p>
      </Desplegable>
      <Desplegable titulo="¿Qué anuncios se descartan?">
        <p>
          Antes de guardar nada se descartan los anuncios <strong>sin posesión</strong>,{' '}
          <strong>okupados u ocupados</strong>, de <strong>nuda propiedad</strong> y las{' '}
          <strong>subastas</strong>. Esos anuncios no se almacenan, así que no aparecen en ninguna vista ni
          cuentan en las medias.
        </p>
      </Desplegable>
      <Desplegable titulo="¿De dónde vienen los datos del mapa de seguridad?">
        <p>
          <strong>Vista criminalidad (por municipio):</strong> usa la <strong>tasa de criminalidad oficial</strong>{' '}
          (infracciones penales × 100 000 hab) publicada por el <strong>Portal Estadístico de Criminalidad</strong>{' '}
          del Ministerio del Interior. Solo tienen publicación oficial los municipios con más de{' '}
          <strong>20 000 habitantes</strong>, por lo que los municipios pequeños aparecen en
          gris. La tasa se calcula anualizado datos de Q1 2026. Fuente: estadisticasdecriminalidad.ses.mir.es
        </p>
        <p>
          <strong>Vista renta (por sección censal / barrio):</strong> usa la{' '}
          <strong>renta neta media por persona</strong> del{' '}
          <strong>Atlas de Distribución de Renta de los Hogares (ADRH 2023)</strong> publicado por el INE en
          octubre de 2025. La sección censal es la unidad geográfica más fina de España (~1 000–2 500 hab), lo que
          permite ver diferencias <strong>dentro</strong> de cada municipio. Verde = renta alta (barrio
          acomodado), rojo = renta baja. ⚠️ Renta no equivale directamente a criminalidad — es un{' '}
          <strong>proxy socioeconómico del barrio</strong>, no un dato policial. Fuente: ine.es/experimental/atlas
        </p>
      </Desplegable>

      <p className="caption">La puntuación es orientativa: ayuda a priorizar, no sustituye una visita.</p>
    </div>
  )
}
