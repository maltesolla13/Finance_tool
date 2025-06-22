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


def calculate_shares(csv_path):
    """
    Berechnet die kumulierten Anteile für jede Sparplanausführung.

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
        - Asset-Klasse
        - Anteile
        - Kumulierte Anteile
    """
    df = pd.read_csv(csv_path, sep=",")

    df["Datum"] = pd.to_datetime(df["datum"])
    df = df.rename(columns={"anteile": "Anteile"})
    df = df.rename(columns={"name": "Sparplan"})
    df = df.rename(columns={"instrument": "Asset-Klasse"})

    df = df.sort_values(by=["Sparplan", "Datum"])
    df["Anteile_kumuliert"] = df.groupby("Sparplan")["Anteile"].cumsum()

    return df[[
        "Datum",
        "Sparplan",
        "Asset-Klasse",
        "Anteile",
        "Anteile_kumuliert"
    ]]


def calculate_depot_value(df):  # Gesamtwert Depot + Gewinn/Verlust
    """
    Bestimmt die Anteile pro Aktie zum Ist-Zeitpunkt und fragt die aktienkurse ab.
    gibt ein DataFrame mit dem dem 

    Input
    -----
    DataFrame 
        - Datum
        - Sparplan
        - Asset-Klasse
        - Anteile
        - Kumulierte Anteile

    Response
    --------
    DataFrame 
    """
    return


def calculate_depot_distribution():
    """
    Ermittelt 
    """
    return
