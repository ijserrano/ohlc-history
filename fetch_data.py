"""
Descarga históricos OHLC (diario y semanal) desde Stooq, sin API key,
y los guarda como JSON en data/. Pensado para ejecutarse a mano o vía
GitHub Actions (ver .github/workflows/update-data.yml).

Uso:
    python fetch_data.py
"""

import csv
import io
import json
import os
import sys
import urllib.request

# Símbolo mostrado -> símbolo Stooq. Añade/quita pares aquí.
SYMBOLS = {
    "XAUUSD": "xauusd",
    "EURUSD": "eurusd",
    "AUDNZD": "audnzd",
    "GBPUSD": "gbpusd",
}

# Código de intervalo Stooq -> etiqueta usada en el nombre de fichero.
# Stooq en su endpoint gratuito solo da granularidad diaria/semanal/mensual
# para forex (no intradía sin cuenta).
INTERVALS = {"d": "1d", "w": "1wk"}

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def fetch_stooq(symbol, interval_code):
    url = f"https://stooq.com/q/d/l/?s={symbol}&i={interval_code}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8")

    if not raw.strip() or raw.strip().lower().startswith("<!doctype"):
        return []

    candles = []
    reader = csv.DictReader(io.StringIO(raw))
    for row in reader:
        try:
            candles.append(
                {
                    "date": row["Date"],
                    "o": float(row["Open"]),
                    "h": float(row["High"]),
                    "l": float(row["Low"]),
                    "c": float(row["Close"]),
                    "v": float(row["Volume"]) if row.get("Volume") else None,
                }
            )
        except (KeyError, ValueError):
            continue
    return candles


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    any_failed = False

    for label, stooq_symbol in SYMBOLS.items():
        for interval_code, interval_label in INTERVALS.items():
            try:
                candles = fetch_stooq(stooq_symbol, interval_code)
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR {label} {interval_label}: {exc}", file=sys.stderr)
                any_failed = True
                continue

            if not candles:
                print(f"WARN: sin datos para {label} {interval_label}", file=sys.stderr)
                any_failed = True
                continue

            out_path = os.path.join(OUT_DIR, f"{label}_{interval_label}.json")
            with open(out_path, "w") as f:
                json.dump(candles, f)
            print(f"OK {label} {interval_label}: {len(candles)} velas -> {out_path}")

    if any_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
