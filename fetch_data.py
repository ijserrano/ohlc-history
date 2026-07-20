"""
Descarga históricos OHLC (diario y semanal) desde la API pública (no oficial,
sin API key) de Yahoo Finance, y los guarda como JSON en data/. Pensado para
ejecutarse a mano o vía GitHub Actions (ver .github/workflows/update-data.yml).

Nota: es el mismo endpoint que usa por debajo la librería `yfinance`. No
requiere key, pero es no-oficial: puede cambiar sin aviso. Si un día deja de
responder, hay que buscar alternativa (ver conversación / README).

Uso:
    python fetch_data.py
"""

import datetime
import json
import os
import sys
import urllib.error
import urllib.request

# Etiqueta mostrada -> símbolo Yahoo Finance.
SYMBOLS = {
    "XAUUSD": "XAUUSD=X",
    "EURUSD": "EURUSD=X",
    "AUDNZD": "AUDNZD=X",
    "GBPUSD": "GBPUSD=X",
}

# interval Yahoo -> etiqueta usada en el nombre de fichero, y rango a pedir.
INTERVALS = {
    "1d": {"label": "1d", "range": "5y"},
    "1wk": {"label": "1wk", "range": "10y"},
}

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

HEADERS = {
    # Yahoo bloquea el User-Agent por defecto de urllib en algunos casos.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_yahoo(symbol, interval, range_):
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?interval={interval}&range={range_}"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc

    data = json.loads(raw)
    chart = data.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(str(chart["error"]))

    result = (chart.get("result") or [None])[0]
    if not result:
        raise RuntimeError(f"respuesta sin 'result': {raw[:300]}")

    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]

    n = len(timestamps)
    opens = quote.get("open") or [None] * n
    highs = quote.get("high") or [None] * n
    lows = quote.get("low") or [None] * n
    closes = quote.get("close") or [None] * n
    volumes = quote.get("volume") or [None] * n

    candles = []
    for i, ts in enumerate(timestamps):
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]
        if None in (o, h, l, c):
            continue
        date = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        candles.append({"date": date, "o": o, "h": h, "l": l, "c": c, "v": volumes[i]})

    return candles


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    any_failed = False

    for label, yahoo_symbol in SYMBOLS.items():
        for interval, cfg in INTERVALS.items():
            try:
                candles = fetch_yahoo(yahoo_symbol, interval, cfg["range"])
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR {label} {cfg['label']}: {exc}", file=sys.stderr)
                any_failed = True
                continue

            if not candles:
                print(f"WARN: sin datos para {label} {cfg['label']}", file=sys.stderr)
                any_failed = True
                continue

            out_path = os.path.join(OUT_DIR, f"{label}_{cfg['label']}.json")
            with open(out_path, "w") as f:
                json.dump(candles, f)
            print(f"OK {label} {cfg['label']}: {len(candles)} velas -> {out_path}")

    if any_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
