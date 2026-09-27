"""Almacén canónico de listings deduplicado por url.

Sustituye el modelo de snapshots diarios acumulativos: un único índice
(`listings.json`) con el estado más reciente de cada piso, más un log de
agregados diarios (`historico_diario.json`) para la vista de tendencia.
"""


def _key(item):
    return item.get("url") or item.get("id") or item.get("title", "")


OUTLIER_DROP_RATIO = (
    0.6  # nuevo_precio / precio_anterior por debajo de esto = bajada >40%, sospechosa
)


def _aplicar_precio(item, old):
    """Decide price/price_drop/previous_price/_candidate_price para `item` dado `old`.

    Regla: price_drop/previous_price se recalculan contra el último precio
    visto (old_price) en cada pasada -- nunca se arrastran de pasadas
    anteriores. Un salto a la baja de más del 40% en una sola pasada no se
    acepta hasta que se confirme con un valor similar en la pasada siguiente.
    """
    old_price = old.get("price")
    new_price = item.get("price")

    if new_price is None:
        item["price"] = old_price
        if "price_drop" in old:
            item["price_drop"] = old["price_drop"]
        if "previous_price" in old:
            item["previous_price"] = old["previous_price"]
        if "_candidate_price" in old:
            item["_candidate_price"] = old["_candidate_price"]
        return

    if not old_price or new_price >= old_price:
        item.pop("price_drop", None)
        item.pop("previous_price", None)
        item.pop("_candidate_price", None)
        return

    es_salto_grande = (new_price / old_price) < OUTLIER_DROP_RATIO
    confirmado = old.get("_candidate_price") == new_price

    if es_salto_grande and not confirmado:
        item["price"] = old_price
        item["_candidate_price"] = new_price
        if "price_drop" in old:
            item["price_drop"] = old["price_drop"]
        if "previous_price" in old:
            item["previous_price"] = old["previous_price"]
        return

    item["price_drop"] = old_price - new_price
    item["previous_price"] = old_price
    item.pop("_candidate_price", None)


def upsert(existing_index, new_listings, today):
    """Fusiona new_listings en existing_index. Devuelve el índice actualizado.

    Por cada url: conserva first_seen original, actualiza last_seen a hoy,
    detecta bajadas de precio, y reactiva pisos delisted que reaparecen.
    """
    index = dict(existing_index)

    for item in new_listings:
        key = _key(item)
        if not key:
            continue

        item = dict(item)
        old = index.get(key)

        if old is not None:
            item["first_seen"] = old.get("first_seen", today)
            _aplicar_precio(item, old)
        else:
            item.setdefault("first_seen", today)

        item["last_seen"] = today
        item["status"] = "active"
        index[key] = item

    return index


def mark_delisted(index, today, threshold_days=7):
    """Marca status='delisted' en los pisos sin last_seen en >= threshold_days."""
    from datetime import date

    hoy = date.fromisoformat(today) if isinstance(today, str) else today
    result = dict(index)

    for item in result.values():
        last_seen = item.get("last_seen")
        if not last_seen:
            continue
        last_seen_date = (
            date.fromisoformat(last_seen) if isinstance(last_seen, str) else last_seen
        )
        dias_sin_ver = (hoy - last_seen_date).days
        if dias_sin_ver >= threshold_days:
            item["status"] = "delisted"

    return result


def append_daily_aggregate(historico, listings, today):
    """Añade (o reemplaza) la fila agregada del día `today` en historico.

    historico: lista de dicts (fecha, count, avg_price, avg_score, min_price, max_price).
    No duplica fecha si ya existe una fila para `today` (se sobrescribe).
    """
    precios = [i["price"] for i in listings if i.get("price") is not None]
    scores = [i["score"] for i in listings if i.get("score") is not None]

    fila = {
        "fecha": today,
        "count": len(listings),
        "avg_price": round(sum(precios) / len(precios)) if precios else None,
        "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
        "min_price": min(precios) if precios else None,
        "max_price": max(precios) if precios else None,
    }

    resultado = [row for row in historico if row.get("fecha") != today]
    resultado.append(fila)
    resultado.sort(key=lambda r: r["fecha"])
    return resultado


def load_listings(path):
    import json

    if not path.exists():
        return {}
    items = json.loads(path.read_text(encoding="utf-8"))
    return {_key(item): item for item in items if _key(item)}


def save_listings(path, index):
    import json

    listado = sorted(index.values(), key=lambda x: x.get("score", 0) or 0, reverse=True)
    path.write_text(json.dumps(listado, ensure_ascii=False, indent=2), encoding="utf-8")


def load_historico(path):
    import json

    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_historico(path, historico):
    import json

    path.write_text(
        json.dumps(historico, ensure_ascii=False, indent=2), encoding="utf-8"
    )
