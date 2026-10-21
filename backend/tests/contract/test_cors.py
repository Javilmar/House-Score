"""T028 - CORS: solo los orígenes de CORS_ORIGINS pueden leer la API desde un navegador."""

from app.core.config import get_settings

FRONT = "https://housescore.pages.dev"
OTRO = "https://malicioso.example"


def test_cors_origins_se_lee_de_la_variable_recortando_y_sin_vacios(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", f" {FRONT} , ,http://localhost:5173,")
    get_settings.cache_clear()
    try:
        assert get_settings().cors_origins == (FRONT, "http://localhost:5173")
    finally:
        get_settings.cache_clear()


def test_cors_origins_vacio_por_defecto(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    get_settings.cache_clear()
    try:
        assert get_settings().cors_origins == ()
    finally:
        get_settings.cache_clear()


def test_origen_permitido_recibe_la_cabecera_en_listings_e_historico(make_client):
    client = make_client(CORS_ORIGINS=FRONT)
    for ruta in ("/listings", "/historico"):
        r = client.get(ruta, headers={"Origin": FRONT})
        assert r.status_code == 200
        assert r.headers.get("access-control-allow-origin") == FRONT


def test_origen_no_permitido_no_recibe_la_cabecera(make_client):
    client = make_client(CORS_ORIGINS=FRONT)
    for ruta in ("/listings", "/historico"):
        r = client.get(ruta, headers={"Origin": OTRO})
        assert "access-control-allow-origin" not in r.headers


def test_preflight_de_post_ingest_no_se_concede(make_client):
    client = make_client(CORS_ORIGINS=FRONT)
    r = client.options(
        "/ingest",
        headers={
            "Origin": FRONT,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert r.status_code == 400
    assert "POST" not in r.headers.get("access-control-allow-methods", "")
