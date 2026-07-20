"""
Descarga históricos OHLC (diario y semanal) desde la API de Twelve Data y los
guarda como JSON en data/. Pensado para ejecutarse vía GitHub Actions, con la
API key inyectada como GitHub Secret (ver .github/workflows/update-data.yml).

La key NUNCA se escribe en este fichero ni en el repo: se lee de la variable
de entorno TWELVEDATA_API_KEY en tiempo de ejecución.

Uso local:
    export TWELVEDATA_API_KEY="tu_key"
    python fetch_data.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Etiqueta mostrada -> símbolo Twelve Data.
SYMBOLS = {
    "XAUUSD": "XAU/USD",
}

# interval Twelve Data -> etiqueta usada en el nombre de fichero.
INTERVALS = {
    "1h": "1h",
    "4h": "4h",
    "1day": "1d",
    "1week": "1wk",
}

OUTPUT_SIZE = 5000  # máximo de velas por petición

# Free tier: 8 peticiones/min. Tenemos 8 llamadas exactas (4 pares x 2
# intervalos), así que espaciamos un poco para no rozar el límite.
SLEEP_BETWEEN_CALLS = 8  # segundos

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def fetch_twelvedata(api_key, symbol, interval, outputsize):
    params = urllib.parse.urlencode(
        {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": api_key,
            "order": "ASC",
        }
    )
    url = f"https://api.twelvedata.com/time_series?{params}"

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc

    data = json.loads(raw)
    if data.get("status") == "error":
        raise RuntimeError(data.get("message", "error desconocido de Twelve Data"))

    values = data.get("values", [])
    candles = []
    for v in values:
        try:
            candles.append(
                {
                    "date": v["datetime"],
                    "o": float(v["open"]),
                    "h": float(v["high"]),
                    "l": float(v["low"]),
                    "c": float(v["close"]),
                    "v": float(v["volume"]) if v.get("volume") else None,
                }
            )
        except (KeyError, ValueError):
            continue
    return candles


def main():
    api_key = os.environ.get("TWELVEDATA_API_KEY")
    if not api_key:
        print("ERROR: falta la variable de entorno TWELVEDATA_API_KEY", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    any_failed = False
    calls_made = 0
    total_calls = len(SYMBOLS) * len(INTERVALS)

    for label, symbol in SYMBOLS.items():
        for interval, file_label in INTERVALS.items():
            if calls_made > 0:
                time.sleep(SLEEP_BETWEEN_CALLS)
            calls_made += 1

            try:
                candles = fetch_twelvedata(api_key, symbol, interval, OUTPUT_SIZE)
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR {label} {file_label}: {exc}", file=sys.stderr)
                any_failed = True
                continue

            if not candles:
                print(f"WARN: sin datos para {label} {file_label}", file=sys.stderr)
                any_failed = True
                continue

            out_path = os.path.join(OUT_DIR, f"{label}_{file_label}.json")
            with open(out_path, "w") as f:
                json.dump(candles, f)
            print(
                f"OK {label} {file_label} ({calls_made}/{total_calls}): "
                f"{len(candles)} velas -> {out_path}"
            )

    if any_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
