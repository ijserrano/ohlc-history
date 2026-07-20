# OHLC Tape — histórico multi-par sin API key

Dashboard estático (para GitHub Pages) que muestra OHLC diario/semanal de varios
pares, incluyendo XAUUSD, usando datos de [Stooq](https://stooq.com) sin necesidad
de ninguna API key.

## Cómo funciona

1. `fetch_data.py` descarga el CSV público de Stooq para cada símbolo y lo
   convierte a `data/<SIMBOLO>_<1d|1wk>.json`.
2. `.github/workflows/update-data.yml` ejecuta ese script automáticamente cada
   día laborable (cron `15 22 * * 1-5`, hora UTC) y comitea los cambios si los hay.
3. `index.html` es una página estática sin dependencias que simplemente hace
   `fetch('data/XAUUSD_1d.json')` etc. — mismo origen, sin CORS, sin llamadas
   externas al cargar.

## Puesta en marcha

```bash
# 1. Genera los datos una primera vez en local
python3 fetch_data.py

# 2. Súbelo todo a un repo de GitHub
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin <tu-repo>
git push -u origin main
```

Luego activa GitHub Pages: **Settings → Pages → Deploy from a branch → main /
(root)**. El Action ya empezará a refrescar `data/` solo, sin que tengas que
tocar nada más.

## Añadir o quitar pares

Edita el diccionario `SYMBOLS` en `fetch_data.py` (símbolo Stooq, en minúsculas,
sin separador — ej. `xauusd`, `eurusd`, `audnzd`). Vuelve a correr el script
(o espera al siguiente run del Action) y añade el símbolo en el campo "Pares"
de la página, o cambia el valor por defecto en `index.html`.

## Notas

- Stooq da granularidad diaria/semanal/mensual gratis para forex — no
  intradía. Si más adelante necesitas velas intradía, hay que cambiar de
  fuente (ver conversación previa sobre OANDA/Yahoo).
- El `Volume` que reporta Stooq para forex no siempre es representativo del
  volumen real de mercado (es agregado del propio proveedor), trátalo como
  orientativo.
