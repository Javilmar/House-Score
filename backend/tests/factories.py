def listing(**over):
    base = {
        "url": "https://ejemplo/piso-1",
        "titulo": "Piso de prueba",
        "precio": 200000,
        "m2": 70,
        "habitaciones": 2,
        "banos": 1,
        "municipio": "getafe",
        "fuente": "pisos.com",
        "score": 65.0,
    }
    base.update(over)
    return base


def pasada(*items):
    return {"listings": list(items)}
