bash

cat /mnt/user-data/outputs/fetch_prices.py
Output

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

TICKERS = {
    "RHM.DE":  "703000",
    "ALV.DE":  "840400",
    "GOOG":    "A14Y6H",
    "BSL.DE":  "510200",
    "EOAN.DE": "ENAG99",
    "ELG.DE":  "567710",
    "EBS.VI":  "909943",
    "FCX":     "896476",
    "EXSG.DE": "263528",
    "MRVL":    "A3CNLD",
    "MOH.AT":  "794038",
    "OMV.VI":  "874341",
    "REP.MC":  "876845",
    "RO.SW":   "A424UK",
    "RUI.PA":  "A2DUVQ",
    "SIX2.DE": "723132",
    "SCCO":    "A0HG1Y",
    "SPYW.DE": "A1JT1B",
    "TSM":     "909800",
    "TGB":     "866869",
    "AMD":     "863186",
}

HOLDINGS = {
    "703000": {"name": "Rheinmetall AG",              "shares": 19.0,       "cost_eur": 9377.45,  "country": "Germany"},
    "840400": {"name": "Allianz SE",                  "shares": 17.04732,   "cost_eur": 5381.74,  "country": "Germany"},
    "A14Y6H": {"name": "Alphabet Inc. C",             "shares": 173.0,      "cost_eur": 27944.82, "country": "USA"},
    "510200": {"name": "Basler AG",                   "shares": 400.0,      "cost_eur": 9014.26,  "country": "Germany"},
    "ENAG99": {"name": "E.ON SE",                     "shares": 310.57868,  "cost_eur": 4100.00,  "country": "Germany"},
    "567710": {"name": "Elmos Semiconductor",         "shares": 32.0,       "cost_eur": 5992.03,  "country": "Germany"},
    "909943": {"name": "Erste Group Bank",            "shares": 74.0,       "cost_eur": 4974.81,  "country": "Austria"},
    "896476": {"name": "Freeport-McMoRan",            "shares": 52.0,       "cost_eur": 2993.47,  "country": "USA"},
    "263528": {"name": "iShares Euro Stoxx Sel.Div.30","shares": 252.321,   "cost_eur": 4364.58,  "country": "Germany"},
    "A3CNLD": {"name": "Marvell Technology",          "shares": 38.0,       "cost_eur": 9819.17,  "country": "USA"},
    "794038": {"name": "Motor Oil (Hellas)",           "shares": 200.0,      "cost_eur": 6007.07,  "country": "Greece"},
    "874341": {"name": "OMV AG",                      "shares": 100.48315,  "cost_eur": 4100.00,  "country": "Austria"},
    "876845": {"name": "Repsol SA",                   "shares": 493.66063,  "cost_eur": 5606.00,  "country": "Spain"},
    "A424UK": {"name": "Roche Holding PS",            "shares": 69.0,       "cost_eur": 20286.36, "country": "Switzerland"},
    "A2DUVQ": {"name": "Rubis SCA",                   "shares": 159.91296,  "cost_eur": 4100.00,  "country": "France"},
    "723132": {"name": "Sixt SE",                     "shares": 2.0,        "cost_eur": 152.05,   "country": "Germany"},
    "A0HG1Y": {"name": "Southern Copper",             "shares": 22.40887,   "cost_eur": 3937.20,  "country": "USA"},
    "A1JT1B": {"name": "SPDR S&P EO Div.Aristocrats", "shares": 2267.296,  "cost_eur": 56795.90, "country": "Ireland"},
    "909800": {"name": "TSMC ADR/5",                  "shares": 71.0,       "cost_eur": 20866.19, "country": "Taiwan"},
    "866869": {"name": "Taseko Mines",                "shares": 530.0,      "cost_eur": 4043.97,  "country": "Canada"},
    "863186": {"name": "AMD Inc.",                    "shares": 40.0,       "cost_eur": 7473.75,  "country": "USA"},
}

DIVIDENDS_NET = {
    "A1JT1B": 218.20 + 1171.16 + 181.97 + 299.17 + 44.99,
    "A14Y6H": (18.61-2.79) + (31.53-4.73) + (30.62-4.59) + (30.94-4.64) + 21.98,
    "909800": 23.68 + 27.59,
    "A424UK": (527.78-79.17) + 483.00,
    "703000": 153.90 + 160.87,
    "876845": (79.44-11.92) + (159.92-23.99) + (73.00-10.95) + 140.80 + 59.13,
    "874341": 404.15 - 60.62,
    "ENAG99": 146.71 + 130.34,
    "794038": (6.79-0.34) + (111.36-5.57) + 33.66,
    "909943": (222.00-33.30) + 40.24,
    "A2DUVQ": 299.40 - 38.32,
    "263528": 5.08 + 8.51 + 90.45 + 51.52 + 13.53 + 13.20,
    "840400": 170.56 + 61.60 + 164.27 + 50.36,
    "723132": 5.40,
    "A0HG1Y": 18.70,
    "896476": 4.65,
    "863186": 0,
    "510200": 0,
    "567710": 0,
    "866869": 0,
    "A3CNLD": 0,
}

USD_TICKERS = {"GOOG", "MRVL", "FCX", "SCCO", "TSM", "TGB", "AMD"}


def get_rate(pair, fallback):
    try:
        t = yf.Ticker(pair)
        r = t.fast_info["lastPrice"]
        return float(r) if r else fallback
    except Exception:
        return fallback


def fetch_prices():
    eurusd = get_rate("EURUSD=X", 1.164)
    chfeur = get_rate("CHFEUR=X", 1.0908)
    print("EUR/USD: %.4f  CHF/EUR: %.4f" % (eurusd, chfeur))

    tickers_list = list(TICKERS.keys())
    data = yf.download(
        tickers_list,
        period="2d",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
    )

    prices_eur = {}
    for symbol, wkn in TICKERS.items():
        try:
            if len(tickers_list) == 1:
                price = float(data["Close"].iloc[-1])
            else:
                price = float(data[symbol]["Close"].iloc[-1])

            if symbol in USD_TICKERS:
                price_eur = price / eurusd
            elif symbol == "RO.SW":
                price_eur = price * chfeur
            else:
                price_eur = price

            prices_eur[wkn] = round(price_eur, 4)
            print("  %s -> %s: %.2f -> EUR %.2f" % (symbol, wkn, price, price_eur))
        except Exception as e:
            print("  WARNING: could not fetch %s: %s" % (symbol, e))

    return prices_eur, eurusd, chfeur


def build_portfolio(prices_eur, eurusd, chfeur):
    positions = []
    total_value = 0.0
    total_cost = 0.0
    total_div = 0.0

    for wkn, holding in HOLDINGS.items():
        price = prices_eur.get(wkn)
        if price is None:
            print("  MISSING price for %s (%s)" % (wkn, holding["name"]))
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
    print("\nSaved -> %s" % out_path)
    print("Total value: EUR %.2f" % portfolio["total_value_eur"])
    print("Total gain:  EUR %.2f (%.2f%%)" % (portfolio["total_gain_eur"], portfolio["total_gain_pct"]))
    print("Dividends:   EUR %.2f" % portfolio["total_div_net_eur"])


if __name__ == "__main__":
    main()
