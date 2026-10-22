# Contrato: vistas y rutas

Una vista por pestaña actual, en el mismo orden. La ruta vive en el hash
(`#/<vista>?<parámetros>`); recargar restaura la vista y sus parámetros.
Ruta desconocida o vacía → `#/listados`.

| Orden | Vista | Ruta | Parámetros (opcionales) | Comportamiento fuente |
|---|---|---|---|---|
| 1 | Listados completos | `#/listados` | `zona`, `muni` (repetibles), `score=min-max`, `precio=min-max`, `hab=min-max`, `retirados=1` | inventario §tabs1 `tab1` |
| 2 | Top scoring | `#/top` | `n` (5–30, por defecto 15), `id` (url del listing a resaltar) | inventario §tabs1 `tab2` |
| 3 | Novedades | `#/novedades` | — | inventario §tabs2 `tab5` |
| 4 | Evolución y análisis | `#/evolucion` | — | inventario §tabs1/§tabs2 `tab3` |
| 5 | Bajadas de precio | `#/bajadas` | `orden` (opciones del selector actual) | inventario §tabs2 `tab4` |
| 6 | Hipoteca | `#/hipoteca` | `precio`, `tipo` (`segunda-mano`\|`obra-nueva`), `ccaa` (`madrid`\|`clm`) | inventario §tabs2 `tab6` |
| 7 | Cómo funciona | `#/como-funciona` | — | inventario §tabs2 `tab7` |
| 8 | Mapas | `#/mapas` | `capa` (`criminalidad`\|`renta`\|`precio`; por defecto la primera con datos, como hoy) | inventario §mapas `tab8` |

## Navegación entre vistas

- Botón **↗** en Listados → `#/top?id=<url>`: abre Top scoring y hace scroll
  al card si está entre los N mostrados (comportamiento de `goToCard`).
- Botón **€ Hipoteca** en Listados, Top scoring, Novedades y Bajadas →
  `#/hipoteca?precio=<precio>&tipo=<tipo>&ccaa=<ccaa>`; la calculadora se
  rellena con esos valores una vez, y los cambios posteriores del usuario no
  se pisan (equivalente a `hip_nav_id`). Corrige la discrepancia del
  inventario: abre Hipoteca, no Bajadas.
- Los parámetros de Listados se escriben en el hash al cambiar un filtro
  (enlace compartible), sin recargar.
