import requests
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


API_URL = "https://extraetf.com/api-v3/stock/quotes/"


def fetch_price_history(isin: str,
                        from_ts: int = None,
                        to_ts: int = None
                        ) -> list[dict]:
    """
    Liest alle Kurs-Einträge für die gegebene ISIN aus und
    gibt eine Liste von {date, price_last}-Dicts zurück.
    Arbeitet die Paginierung automatisch über 'next' ab.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"stock": isin}
    if from_ts:
        params["fromTs"] = from_ts
    if to_ts:
        params["toTs"] = to_ts

    all_history = []
    url = API_URL

    while True:
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        # 1) Ergebnisliste extrahieren
        batch = data.get("results", [])
        # 2) Filter auf die gewünschte ISIN (falls API ungefiltert liefert)
        batch = [q for q in batch if q.get("stock") == isin]

        # 3) Datum + Schlusskurs sammeln
        for q in batch:
            all_history.append({
                "date": q["date"],
                "price_last": q["price_last"]
            })

        # 4) Nächste Seite? 'next' ist schon eine vollständige URL
        next_url = data.get("next")
        if not next_url:
            break

        # Für die nächste Iteration: URL wechseln, Params nur beim ersten
        # Durchgang
        url = next_url
        params = {}

    return all_history


if __name__ == "__main__":
    six_months_ago = datetime.now(timezone.utc) - relativedelta(months=6)
    from_ts = int(six_months_ago.timestamp() * 1000)
    isin = "DE0007100000"
    history = fetch_price_history(isin, from_ts=from_ts)

    for entry in history:
        print(entry["date"], "→", entry["price_last"], "€")

    if not history:
        print("Keine Kursdaten gefunden.")
    else:
        # Beispiel: Nur die letzten 5 Einträge ausgeben
        for entry in history[-5:]:
            dt = datetime.fromisoformat(entry["date"])
            print(f"{dt:%Y-%m-%d %H:%M} → {entry['price_last']} €")
