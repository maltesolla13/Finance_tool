import requests
import json

base_url = "https://extraetf.com/de/"

etf = "etf-profile/"
aktie = "stock-profile/"
crypto = "crypto-profile/"

MB = "DE0007100000"
NVIDIA = "US67066G1040"
CORE_DAX = "DE0005933931"

MB_request = f"{base_url}{aktie}{MB}"

response = requests.get(MB_request)

if response.status_code == 200:
    # 3a. Wenn JSON zurückkommt (Content-Type application/json), dann so:
    try:
        data = response.json()
        print("JSON-Daten:", json.dumps(data, indent=2, ensure_ascii=False))
    except ValueError:
        # 3b. Andernfalls als reinen Text (HTML) ausgeben
        print("Text-Antwort:", response.text[:500], "…")
else:
    print(f"Fehler bei der Anfrage: HTTP {response.status_code}")
