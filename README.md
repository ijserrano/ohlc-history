# OHLC History — histórico multi-par vía Twelve Data

Dashboard estático (para GitHub Pages) que muestra OHLC diario/semanal de varios
pares, incluyendo XAUUSD, usando la [API de Twelve Data](https://twelvedata.com/docs)
(key gratuita e instantánea, sin aprobación previa).

## Cómo funciona

1. `fetch_data.py` pide velas D1/W1 a Twelve Data para cada símbolo y las
   guarda como `data/<SIMBOLO>_<1d|1wk>.json`.
2. `.github/workflows/update-data.yml` ejecuta ese script automáticamente cada
   día laborable (cron `15 22 * * 1-5`, hora UTC) y comitea los cambios si los hay.
3. `index.html` es una página estática sin dependencias que simplemente hace
   `fetch('data/XAUUSD_1d.json')` etc. — mismo origen, sin CORS, sin llamadas
   externas al cargar. La API key **nunca llega al navegador**: solo la usa
   el script en el servidor (GitHub Actions).

## Puesta en marcha

1. Regístrate en https://twelvedata.com/apikey (plan Basic/free) — la key
   aparece al instante en tu dashboard, sin esperar aprobación.
2. En tu repo de GitHub: **Settings → Secrets and variables → Actions →
   New repository secret** → nombre `TWELVEDATA_API_KEY`, valor la key.
3. Sube los ficheros (`index.html`, `fetch_data.py`, `README.md`,
   `.github/workflows/update-data.yml`) al repo.
4. En la pestaña **Actions**, ejecuta manualmente "Update market data" (botón
   "Run workflow") para generar el `data/` inicial.
5. Activa GitHub Pages: **Settings → Pages → Deploy from a branch → main /
   (root)**.

   > Si tu cuenta de GitHub está bajo una organización Enterprise, Pages en
   > repos **privados** puede pedir upgrade de pago. La forma gratuita de
   > evitarlo es hacer el repo público (**Settings → General → Danger
   > Zone → Change visibility → Make public**) — es seguro porque la API
   > key vive solo en el Secret, nunca en el código. Si prefieres no hacer
   > público un repo colgado de tu cuenta de trabajo, créalo en tu cuenta
   > personal de GitHub en su lugar, donde Pages en repos públicos es
   > gratis sin restricciones.

Para probarlo en local en vez de esperar al Action:

```bash
export TWELVEDATA_API_KEY="tu_key"
python3 fetch_data.py
```

## Añadir o quitar pares

Edita el diccionario `SYMBOLS` en `fetch_data.py` (formato Twelve Data, con
barra — ej. `XAU/USD`, `EUR/USD`, `AUD/NZD`). Vuelve a correr el script (o
espera al siguiente run del Action) y añade el símbolo en el campo "Pares"
de la página, o cambia el valor por defecto en `index.html`.

## Notas

- Por ahora solo se descarga **XAUUSD**. Para añadir más pares, agrégalos
  al diccionario `SYMBOLS` en `fetch_data.py` (formato Twelve Data, con
  barra — ej. `EUR/USD`) y al campo "Pares" de `index.html`.
- Free tier: **8 peticiones/min, 800/día**. Con 1 par × 4 intervalos (H1,
  H4, D1, W1) son 4 llamadas por ejecución — el script mete una pausa de
  8s entre cada una para no rozar el límite de 8/min. Si añades más pares
  o temporalidades, ajusta `SLEEP_BETWEEN_CALLS` o reparte las llamadas en
  varias ejecuciones.
- En el free tier, el histórico intradía (H1/H4) suele tener menos
  profundidad que D1/W1 (normalmente varios meses hacia atrás, no años) —
  no es un error si ves menos velas ahí que en diario.
- `outputsize=5000` es el máximo por petición; si Twelve Data devuelve menos
  para algún par/intervalo (histórico más corto o límite del plan), no es
  un error del script.


