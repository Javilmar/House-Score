# Dashboard de Búsqueda de Vivienda

Dashboard en Streamlit que visualiza listings de vivienda (Madrid Sur + Toledo
Norte) con scoring a medida. Los datos los genera periódicamente un script en el
ordenador local y se publican a este repo para que el dashboard en la nube
siempre muestre lo último.

## Estructura

```
house-dashboard/
├── dashboard/app.py        # la app Streamlit
├── dashboard/guardar.py    # guarda una pasada y empuja los datos a GitHub
├── datos/                  # JSON diarios (los lee el dashboard)
└── requirements.txt
```

## Ver en local

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Desplegar en Streamlit Community Cloud (gratis)

1. Sube este repo a GitHub.
2. Entra en https://share.streamlit.io con tu cuenta de GitHub.
3. **New app** → elige el repo, rama `main`, y **Main file path** = `dashboard/app.py`.
4. Deploy. Obtienes una URL pública (`tu-app.streamlit.app`).

Cada vez que el script local empuja datos nuevos (ver abajo), Streamlit
redespliega solo y muestra lo último — funcione o no tu ordenador.

## Actualización automática de datos

El script periódico que ya corre en local termina llamando a `guardar.py`, que
escribe el JSON del día y hace `git commit` + `git push` automáticamente. No hay
nada manual que hacer tras el primer despliegue.

## Acceso privado (opcional)

Si no quieres que los datos sean públicos, pon el repo en privado y añade una
contraseña en Streamlit Cloud vía `Settings → Secrets`.
