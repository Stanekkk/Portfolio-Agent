bash

cat /home/claude/portfolio-agent/scripts/fetch_prices.py
Output

"""
Portfolio Agent — fetch_prices.py
Fetches live prices for all positions and writes updated portfolio JSON.
Run daily via GitHub Actions or manually.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

# ── Ticker map  (Yahoo Finance symbol → your WKN) ─────────────────────────────
# Tradegate/Xetra symbols work best for European stocks
TICKERS = {
    "RHM.DE":   "703000",   # Rheinmetall
    "ALV.DE":   "840400",   # Allianz
    "GOOG":     "A14Y6H",   # Alphabet C
    "BSL.DE":   "510200",   # Basler AG
    "EOAN.DE":  "ENAG99",   # E.ON
    "ELG.DE":   "567710",   # Elmos Semiconductor
    "EBS.VI":   "909943",   # Erste Group
    "FCX":      "896476",   # Freeport-McMoRan
    "EXSG.DE":  "263528",   # iShares Euro Stoxx Sel.Div.30  (EXSG on Xetra)
    "MRVL":     "A3CNLD",   # Marvell Technology
    "MOH.AT":   "794038",   # Motor Oil Hellas
    "OMV.VI":   "874341",   # OMV
    "REP.MC":   "876845",   # Repsol
    "RO.SW":    "A424UK",   # Roche PS (Partizipationsschein)
    "RUI.PA":   "A2DUVQ",   # Rubis
    "SIX2.DE":  "723132",   # Sixt
    "SCCO":     "A0HG1Y",   # Southern Copper
    "SPYW.DE":  "A1JT1B",   # SPDR Euro Dividend Aristocrats
    "TSM":      "909800",   # TSMC ADR/5
    "TGB":      "866869",   # Taseko Mines
    "AMD":      "863186",   # AMD
}

# ── Static holdings (shares) — update after trades ────────────────────────────
HOLDINGS = {
    "703000":  {"name": "Rheinmetall AG",           "shares": 19.0,       "cost_eur": 9377.45,   "country": "Germany"},
    "840400":  {"name": "Allianz SE",               "shares": 17.04732,   "cost_eur": 5381.74,   "country": "Germany"},
    "A14Y6H":  {"name": "Alphabet Inc. C",          "shares": 173.0,      "cost_eur": 27944.82,  "country": "USA"},
    "510200":  {"name": "Basler AG",                "shares": 400.0,      "cost_eur": 9014.26,   "country": "Germany"},
    "ENAG99":  {"name": "E.ON SE",                  "shares": 310.57868,  "cost_eur": 4100.00,   "country": "Germany"},
    "567710":  {"name": "Elmos Semiconductor",      "shares": 32.0,       "cost_eur": 5992.03,   "country": "Germany"},
    "909943":  {"name": "Erste Group Bank",         "shares": 74.0,       "cost_eur": 4974.81,   "country": "Austria"},
    "896476":  {"name": "Freeport-McMoRan",         "shares": 52.0,       "cost_eur": 2993.47,   "country": "USA"},
    "263528":  {"name": "iShares Euro Stoxx Sel.Div.30", "shares": 252.321, "cost_eur": 4364.58, "country": "Germany"},
    "A3CNLD":  {"name": "Marvell Technology",       "shares": 38.0,       "cost_eur": 9819.17,   "country": "USA"},
    "794038":  {"name": "Motor Oil (Hellas)",        "shares": 200.0,      "cost_eur": 6007.07,   "country": "Greece"},
    "874341":  {"name": "OMV AG",                   "shares": 100.48315,  "cost_eur": 4100.00,   "country": "Austria"},
    "876845":  {"name": "Repsol SA",                "shares": 493.66063,  "cost_eur": 5606.00,   "country": "Spain"},
    "A424UK":  {"name": "Roche Holding PS",         "shares": 69.0,       "cost_eur": 20286.36,  "country": "Switzerland"},
    "A2DUVQ":  {"name": "Rubis SCA",                "shares": 159.91296,  "cost_eur": 4100.00,   "country": "France"},
    "723132":  {"name": "Sixt SE",                  "shares": 2.0,        "cost_eur": 152.05,    "country": "Germany"},
    "A0HG1Y":  {"name": "Southern Copper",          "shares": 22.40887,   "cost_eur": 3937.20,   "country": "USA"},
    "A1JT1B":  {"name": "SPDR S&P EO Div.Aristocrats", "shares": 2267.296, "cost_eur": 56795.90, "country": "Ireland"},
    "909800":  {"name": "TSMC ADR/5",               "shares": 71.0,       "cost_eur": 20866.19,  "country": "Taiwan"},
    "866869":  {"name": "Taseko Mines",             "shares": 530.0,      "cost_eur": 4043.97,   "country": "Canada"},
    "863186":  {"name": "AMD Inc.",                 "shares": 40.0,       "cost_eur": 7473.75,   "country": "USA"},
}

# ── Accumulated net dividends (update when new payments arrive) ───────────────
DIVIDENDS_NET = {
    "A1JT1B":  218.20 + 1171.16 + 181.97 + 299.17 + 44.99,
    "A14Y6H":  (18.61-2.79) + (31.53-4.73) + (30.62-4.59) + (30.94-4.64) + 21.98,
    "909800":  23.68 + 27.59,
    "A424UK":  (527.78-79.17) + 483.00,
    "703000":  153.90 + 160.87,
    "876845":  (79.44-11.92) + (159.92-23.99) + (73.00-10.95) + 140.80 + 59.13,
    "874341":  404.15 - 60.62,
    "ENAG99":  146.71 + 130.34,
    "794038":  (6.79-0.34) + (111.36-5.57) + 33.66,
    "909943":  (222.00-33.30) + 40.24,
    "A2DUVQ":  299.40 - 38.32,
    "263528":  5.08 + 8.51 + 90.45 + 51.52 + 13.53 + 13.20,
    "840400":  170.56 + 61.60 + 164.27 + 50.36,
    "723132":  5.40,
    "A0HG1Y":  18.70,
    "896476":  4.65,
    "863186":  0,
    "510200":  0,
    "567710":  0,
    "866869":  0,
    "A3CNLD":  0,
}


def get_eur_usd() -> float:
    """Fetch live EUR/USD rate."""
    try:
        ticker = yf.Ticker("EURUSD=X")
        rate = ticker.fast_info["lastPrice"]
        return float(rate) if rate else 1.164
    except Exception:
        return 1.164  # fallback


def get_chf_eur() -> float:
    """Fetch live CHF/EUR rate."""
    try:
        ticker = yf.Ticker("CHFEUR=X")
        rate = ticker.fast_info["lastPrice"]
        return float(rate) if rate else 1.0908
    except Exception:
        return 1.0908


def fetch_prices() -> dict:
    """Fetch latest prices for all tickers, return {wkn: price_eur}."""
    eurusd = get_eur_usd()
    chfeur = get_chf_eur()

    print(f"EUR/USD: {eurusd:.4f}  CHF/EUR: {chfeur:.4f}")

    prices_eur = {}
    tickers_list = list(TICKERS.keys())

    # Batch fetch
    data = yf.download(
        tickers_list,
        period="2d",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
    )

    for symbol, wkn in TICKERS.items():
        try:
            if len(tickers_list) == 1:
                price = float(data["Close"].iloc[-1])
            else:
                price = float(data[symbol]["Close"].iloc[-1])

            # Currency conversion
            if symbol in ("GOOG", "MRVL", "FCX", "SCCO", "TSM", "TGB", "AMD"):
                price_eur = price / eurusd
            elif symbol == "RO.SW":
                price_eur = price * chfeur
            else:
                price_eur = price  # already EUR

            prices_eur[wkn] = round(price_eur, 4)
            print(f"  {symbol:12s} → WKN {wkn}: {price:.2f} → €{price_eur:.2f}")
        except Exception as e:
            print(f"  WARNING: could not fetch {symbol}: {e}")

    return prices_eur, eurusd, chfeur


def build_portfolio(prices_eur: dict, eurusd: float, chfeur: float) -> dict:
    """Combine prices with holdings to build portfolio snapshot."""
    positions = []
    total_value = 0.0
    total_cost = 0.0
    total_div = 0.0

    for wkn, holding in HOLDINGS.items():
        price = prices_eur.get(wkn)
        if price is None:
            print(f"  MISSING price for {wkn} ({holding['name']})")
            continue

        value = holding["shares"] * price
        cost = holding["cost_eur"]
        div = DIVIDENDS_NET.get(wkn, 0.0)
        gain = value - cost
        gain_pct = (gain / cost * 100) if cost else 0

        positions.append({
            "wkn": wkn,
            "name": holding["name"],
            "country": holding["country"],
            "shares": holding["shares"],
            "price_eur": price,
            "value_eur": round(value, 2),
            "cost_eur": cost,
            "gain_eur": round(gain, 2),
            "gain_pct": round(gain_pct, 2),
            "div_net_eur": round(div, 2),
        })

        total_value += value
        total_cost += cost
        total_div += div

    positions.sort(key=lambda x: x["value_eur"], reverse=True)

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "eurusd": eurusd,
        "chfeur": chfeur,
        "total_value_eur": round(total_value, 2),
        "total_cost_eur": round(total_cost, 2),
        "total_gain_eur": round(total_value - total_cost, 2),
        "total_gain_pct": round((total_value - total_cost) / total_cost * 100, 2),
        "total_div_net_eur": round(total_div, 2),
        "positions": positions,
    }


def main():
    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(exist_ok=True)

    print("Fetching prices...")
    prices_eur, eurusd, chfeur = fetch_prices()

    print("\nBuilding portfolio snapshot...")
    portfolio = build_portfolio(prices_eur, eurusd, chfeur)

    out_path = out_dir / "portfolio.json"
    out_path.write_text(json.dumps(portfolio, indent=2, ensure_ascii=False))
    print(f"\nSaved → {out_path}")
    print(f"Total value: €{portfolio['total_value_eur']:,.2f}")
    print(f"Total gain:  €{portfolio['total_gain_eur']:,.2f} ({portfolio['total_gain_pct']:.2f}%)")
    print(f"Dividends:   €{portfolio['total_div_net_eur']:,.2f}")


if __name__ == "__main__":
    main()
Done
The text above is the full file content. Here's what to do:

Go to your repo → Add file → Create new file
Type scripts/fetch_prices.py as the filename
Click inside the text area
Now scroll up in this chat to the grey code block above
Click anywhere inside it, press Ctrl+A to select all the text in it, then Ctrl+C
Paste into GitHub with Ctrl+V
Click Commit changes
