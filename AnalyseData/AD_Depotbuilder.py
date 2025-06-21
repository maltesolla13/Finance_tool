import pandas as pd


def calculate_input(csv_path):
    """
    Berechnet den kumulierten Buy-In für jedes BuyIn-Datum und Sparplan.

    Input
    -----
    str
        mit ablage/namen des Files. hier nicht benötigt, da csv auf gleicher
        ebene wie main.py

    Response
    --------
    DataFrame mit
        - Datum
        - Sparplan
        - BuyIn
        - Kumulierten BuyIn
    """
    df = pd.read_csv(csv_path, sep=",")

    df["Datum"] = pd.to_datetime(df["datum"])
    df = df.rename(columns={"preis": "BuyIn"})
    df = df.rename(columns={"name": "Sparplan"})

    df = df.sort_values(by=["Sparplan", "Datum"])
    df["BuyIn_kumuliert"] = df.groupby("Sparplan")["BuyIn"].cumsum()

    return df[["Datum", "Sparplan", "BuyIn", "BuyIn_kumuliert"]]


def calculate_shares():  # Aktueller Wert + Performance pro Wertpapier
    return


def calculate_depot_value():  # Gesamtwert Depot + Gewinn/Verlust
    return


def calculate_depot_distribution():  # Anteile (Aktie/ETF/Krypto in %)
    return
