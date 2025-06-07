import requests
from datetime import datetime


def fetch_price_history(
        isin: str, from_ts: int = None, to_ts: int = None) -> list[dict]:
    """
    Liefert die Kursentwicklung (price_last) als Liste von Dicts mit Datum
    und Preis.
    Optional mit fromTs/toTs (ms seit Epoch) zur Zeitraum-Filterung.
    """
    url = "https://extraetf.com/api-v3/stock/quotes/"
    params = {"stock": isin}
    if from_ts:
        params["fromTs"] = from_ts
    if to_ts:
        params["toTs"] = to_ts

    resp = requests.get(
        url, params=params, headers={"User-Agent": "Mozilla/5.0"})
    print("Request URL:", resp.url)
    print("HTTP Status:", resp.status_code)
    print("Content-Type:", resp.headers.get("Content-Type"))
    print("Raw JSON:", resp.text[:500], "…")
    resp.raise_for_status()
    data = resp.json()
    print("JSON-Keys:", data.keys())

    resp.raise_for_status()            # wirft bei HTTP-Fehlern
    data = resp.json()

    # 'd' ist das Array mit den Quote-Objekten
    history = data.get("d", [])
    # extrahiere nur Datum und Schlusskurs
    return [
        {
            "date":       q["date"],         # ISO-String
            "price_last": q["price_last"]    # Schlusskurs
        }
        for q in history
    ]


if __name__ == "__main__":
    isin = "DE0007100000"
    history = fetch_price_history(isin)
    for entry in history:
        dt = datetime.fromisoformat(entry["date"])
        print(f"{dt:%Y-%m-%d %H:%M} → {entry['price_last']} €")
