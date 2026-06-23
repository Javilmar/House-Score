"""
build_mapa_assets.py
====================
Descarga y prepara los activos que necesita la pestaña "Mapa de seguridad":

  dashboard/assets/municipios_zona.geojson
      Límites municipales (polígonos) de los municipios considerados en
      Madrid Sur y Toledo Norte, obtenidos de la API pública de OpenDataSoft
      (dataset georef-spain-municipio, CC-BY-4.0).

  dashboard/assets/criminalidad.csv
      Tasa de criminalidad (infracciones penales × 100 000 hab) de los
      municipios con publicación oficial (>20 000 hab).
      Fuente: Portal Estadístico de Criminalidad, Ministerio del Interior.
      Período: Q1 2026 (enero-marzo 2026), anualizado × 4.
      Nota: municipios con menos de 20 000 habitantes no tienen publicación
            oficial y aparecen como NaN en el CSV → gris en el mapa.

  dashboard/assets/secciones_renta.geojson
      Polígonos de secciones censales con renta neta media por persona (€/año)
      del Atlas de Distribución de Renta de los Hogares (ADRH 2023), INE.
      Fuente: ArcGIS Feature Service público de INE España
        (services7.arcgis.com/SEjlCWTAIsMEEXNx — ADRH_2023_Renta_media_por_persona,
        capa 3 = sección censal). CC BY 4.0.
      Clave geográfica: CUSEC (10 dígitos). CUMUN (5 dígitos) = cod_ine.
      Nota: el INE no publica renta para secciones con muy poca población
            → aparecen con renta=null (gris en el mapa).

Uso:
    cd house-dashboard/dashboard
    python scripts/build_mapa_assets.py

Para actualizar la tasa de criminalidad con datos más recientes:
  1. Consultar https://estadisticasdecriminalidad.ses.mir.es
  2. Editar el dict CRIME_Q1 con los nuevos "hechos conocidos"
  3. Ajustar PERIODO y ejecutar de nuevo.

Para actualizar la renta (publicación anual INE, normalmente octubre):
  1. Confirmar que el servicio ArcGIS sigue en la misma URL.
  2. Ajustar ANIO_ADRH y el nombre del FeatureServer si el INE lo rota.
  3. Ejecutar de nuevo.
"""

import json
import math
import time
import unicodedata
from pathlib import Path

import requests

# ── Rutas ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent          # .../dashboard/
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

# ── Municipios considerados (espejo de app.py) ──────────────────────────────
# INE codes: 28XXX = Madrid, 45XXX = Toledo
# (Obtenidos de la tabla INE de relación municipios 2024)
MUNICIPIOS_INE = {
    # Madrid Sur  (códigos INE verificados contra OpenDataSoft georef-spain-municipio)
    "28007": "Alcorcón",
    "28040": "Ciempozuelos",
    "28058": "Fuenlabrada",
    "28065": "Getafe",
    "28015": "Arroyomolinos",
    "28017": "Batres",
    "28050": "Cubas de la Sagra",
    "28066": "Griñón",
    "28073": "Humanes de Madrid",
    "28089": "Moraleja de Enmedio",
    "28140": "Serranillos del Valle",
    "28074": "Leganés",
    "28092": "Móstoles",
    "28096": "Navalcarnero",
    "28106": "Parla",
    "28113": "Pinto",
    "28149": "Torrejón de la Calzada",
    "28161": "Valdemoro",
    # Toledo Norte
    "45002": "Alameda de la Sagra",
    "45014": "Añover de Tajo",
    "45019": "Bargas",
    "45023": "Burguillos de Toledo",
    "45025": "Cabañas de la Sagra",
    "45038": "Carranque",
    "45041": "Casarrubios del Monte",
    "45047": "Cedillo del Condado",
    "45051": "Cobeja",
    "45052": "Cobisa",
    "45056": "Chozas de Canales",
    "45064": "Esquivias",
    "45081": "Illescas",
    "45085": "Lominchar",
    "45088": "Magán",
    "45102": "Mocejón",
    "45119": "Numancia de la Sagra",
    "45122": "Olías del Rey",
    "45128": "Pantoja",
    "45145": "Recas",
    "45161": "Seseña",
    "45176": "Ugena",
    "45180": "Valmojado",
    "45188": "Villaluenga de la Sagra",
    "45199": "El Viso de San Juan",
    "45201": "Yeles",
    "45203": "Yuncler",
    "45204": "Yunclillos",
    "45205": "Yuncos",
}

# ── Datos de criminalidad ────────────────────────────────────────────────────
# Fuente: Portal Estadístico de Criminalidad (Ministerio del Interior)
# Métrica: "Hechos conocidos" (infracciones penales totales) — Q1 2026 (ene-mar)
# URL de consulta:
#   https://estadisticasdecriminalidad.ses.mir.es/sec/jaxiPx/Tabla.htm
#     ?path=/DatosBalanceAct/l0/&file=09003.px&type=pcaxis&L=0
# Solo municipios con publicación oficial (>20 000 hab).
# Nota: los datos Q1 se anualizan × 4 para comparar con la población anual.
PERIODO = "Q1 2026 (ene-mar), anualizado"
FUENTE = "Portal Estadístico de Criminalidad - Ministerio del Interior"

# hechos_conocidos_q1: (hechos_conocidos_Q1_2026, poblacion_ine_2024_aprox)
# Población fuente: Padrón Municipal INE 2024 (revisión a 1-ene-2024).
CRIME_Q1 = {
    # cod_ine: (hechos_q1, población_ine_2024)
    # Códigos INE verificados contra georef-spain-municipio (OpenDataSoft)
    "28007": (1413, 171_500),   # Alcorcón
    "28040": (255,   24_300),   # Ciempozuelos
    "28058": (1067, 197_200),   # Fuenlabrada
    "28065": (1774, 185_500),   # Getafe
    "28074": (1837, 191_300),   # Leganés
    "28092": (1488, 210_700),   # Móstoles
    "28096": (262,   27_400),   # Navalcarnero
    "28106": (1571, 131_000),   # Parla
    "28113": (539,   51_800),   # Pinto
    "28161": (753,   38_200),   # Valdemoro
    "45081": (382,   31_100),   # Illescas
    "45161": (322,   23_500),   # Seseña
    # Sin publicación oficial (<20 000 hab): Griñón, Humanes, Torrejón de la
    # Calzada y todos los municipios pequeños de Toledo Norte.
}


def tasa_100k(hechos_q1: int, poblacion: int) -> float:
    """Anualiza los hechos de un trimestre y los normaliza por 100 000 hab."""
    return round(hechos_q1 * 4 / poblacion * 100_000, 1)


# ── Constantes para la capa de renta por sección censal ─────────────────────
# ArcGIS Feature Service público del INE — Atlas de Distribución de Renta de
# los Hogares (ADRH 2023), capa 3 = sección censal.
# Campos clave: CUSEC (10 díg.), CUMUN (5 díg. = cod_ine), dato1 = renta media
# neta por persona (€/año), indicador1 = "Renta neta media por persona".
ARCGIS_ADRH_URL = (
    "https://services7.arcgis.com/SEjlCWTAIsMEEXNx/arcgis/rest/services"
    "/ADRH_2023_Renta_media_por_persona/FeatureServer/3/query"
)
ANIO_ADRH = "2023"
FUENTE_ADRH = "Atlas de Distribución de Renta de los Hogares - INE"


# ── 1. Descarga del GeoJSON ──────────────────────────────────────────────────

def _sin_acentos(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def descargar_geojson() -> None:
    print("→ Descargando límites municipales (OpenDataSoft)…")
    base = (
        "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets"
        "/georef-spain-municipio/records"
    )
    target_codes = set(MUNICIPIOS_INE.keys())
    features = []
    offset = 0
    limit = 100

    while True:
        params = {
            "where": 'prov_code="28" OR prov_code="45"',
            "select": "mun_name,mun_code,geo_shape",
            "limit": limit,
            "offset": offset,
        }
        resp = requests.get(base, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        records = data.get("results", [])
        if not records:
            break

        for rec in records:
            code = rec.get("mun_code", "")
            if code not in target_codes:
                continue
            geo_shape = rec.get("geo_shape")
            if not geo_shape:
                continue
            geometry = geo_shape.get("geometry") if isinstance(geo_shape, dict) else None
            if not geometry:
                continue
            features.append({
                "type": "Feature",
                "properties": {
                    "cod_ine": code,
                    "nombre": rec.get("mun_name", MUNICIPIOS_INE.get(code, code)),
                },
                "geometry": geometry,
            })

        offset += limit
        if len(records) < limit:
            break
        time.sleep(0.2)   # cortesía al servidor público

    found_codes = {f["properties"]["cod_ine"] for f in features}
    missing = target_codes - found_codes
    if missing:
        print(f"  ⚠ Sin geometría para: {', '.join(sorted(missing))}")

    geojson = {"type": "FeatureCollection", "features": features}
    out = ASSETS / "municipios_zona.geojson"
    out.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    print(f"  ✓ {len(features)} municipios → {out.relative_to(ROOT.parent)}")


# ── 2. CSV de criminalidad ───────────────────────────────────────────────────

def generar_csv() -> None:
    print("→ Generando criminalidad.csv…")
    lines = [
        "# Tasa de criminalidad por municipio",
        f"# Fuente: {FUENTE}",
        f"# Periodo: {PERIODO}",
        "# Municipios sin publicacion oficial (<20 000 hab) no aparecen en este fichero",
        "cod_ine,municipio,tasa_criminalidad,periodo,fuente",
    ]
    for cod, (hechos, pob) in sorted(CRIME_Q1.items()):
        nombre = MUNICIPIOS_INE.get(cod, cod)
        tasa = tasa_100k(hechos, pob)
        lines.append(f'{cod},{nombre},{tasa},"{PERIODO}","{FUENTE}"')

    out = ASSETS / "criminalidad.csv"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  ✓ {len(CRIME_Q1)} municipios → {out.relative_to(ROOT.parent)}")
    # Preview
    for cod, (hechos, pob) in sorted(CRIME_Q1.items(),
                                     key=lambda x: -tasa_100k(x[1][0], x[1][1])):
        nombre = MUNICIPIOS_INE.get(cod, cod)
        tasa = tasa_100k(hechos, pob)
        print(f"    {nombre:30s} {tasa:7.1f} / 100 000 hab")


# ── 3. Descarga de secciones censales con renta (ADRH 2023) ─────────────────

def descargar_secciones_renta() -> None:
    """Descarga secciones censales + renta media por persona del ADRH 2023 (INE).

    Fuente: ArcGIS Feature Service público services7.arcgis.com/SEjlCWTAIsMEEXNx
    Capa 3 = secciones censales.  GeoJSON resultante incluye geometría + renta
    en properties → un único fichero para el choropleth de app.py.
    """
    print("→ Descargando secciones censales con renta media (ADRH 2023)…")
    target_codes = set(MUNICIPIOS_INE.keys())

    # Filtro WHERE por código municipal — evita descargar toda España
    codes_sql = ", ".join(f"'{c}'" for c in sorted(target_codes))
    where = f"CUMUN IN ({codes_sql})"
    out_fields = "CUSEC,CUMUN,NMUN,dato1"

    features = []
    offset = 0
    limit = 1000   # máximo que admite el servicio por petición

    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": limit,
        }
        resp = requests.get(ARCGIS_ADRH_URL, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("features", [])
        if not batch:
            break

        for feat in batch:
            props = feat.get("properties") or {}
            cusec = props.get("CUSEC") or props.get("cusec", "")
            cumun = props.get("CUMUN") or props.get("cumun", "")
            if cumun not in target_codes:
                continue
            renta = props.get("dato1")   # None si el INE no lo publica

            features.append({
                "type": "Feature",
                "properties": {
                    "cusec":         cusec,
                    "cod_ine":       cumun,
                    "municipio":     MUNICIPIOS_INE.get(cumun, cumun),
                    "renta_persona": renta,
                    "anio":          ANIO_ADRH,
                },
                "geometry": feat.get("geometry"),
            })

        # El servicio señala si hay más páginas
        if not data.get("exceededTransferLimit", False):
            break
        offset += limit
        time.sleep(0.3)   # cortesía al servidor público

    found_codes = {f["properties"]["cod_ine"] for f in features}
    missing = target_codes - found_codes
    if missing:
        print(f"  ⚠ Sin secciones para: {', '.join(sorted(missing))}")

    n_con_dato = sum(1 for f in features if f["properties"]["renta_persona"] is not None)
    geojson = {"type": "FeatureCollection", "features": features}
    out = ASSETS / "secciones_renta.geojson"
    out.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    print(
        f"  ✓ {len(features)} secciones · {len(found_codes)} municipios · "
        f"{n_con_dato} con dato de renta → {out.relative_to(ROOT.parent)}"
    )
    # Preview
    from collections import defaultdict
    per_mun = defaultdict(list)
    for f in features:
        p = f["properties"]
        if p["renta_persona"] is not None:
            per_mun[p["municipio"]].append(p["renta_persona"])
    for mun, vals in sorted(per_mun.items()):
        media = sum(vals) / len(vals)
        print(f"    {mun:30s}  {len(vals):3d} sec  media {media:7.0f} €/pers")


# ── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    descargar_geojson()
    generar_csv()
    descargar_secciones_renta()
    print("\n✓ Assets listos en dashboard/assets/")
