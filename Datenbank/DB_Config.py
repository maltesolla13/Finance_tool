import os
import sqlite3


def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "finance_tracker.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Konten
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS konten (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # Kategorien
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kategorien (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # AusgabenTypen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ausgabentypen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # Laden
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS laden (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    # WertpapierInfo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wertpapierinfo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        isin TEXT NOT NULL,
        ticker TEXT NOT NULL,
        instrument TEXT NOT NULL
    )
    """)

    # Kurs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aktien_id INTEGER NOT NULL,
        kurs REAL NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (aktien_id) REFERENCES wertpapierinfo(id)
    )
    """)

    # Kontobewegung
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kontobewegung (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        betrag REAL NOT NULL,
        kategorie_id INTEGER,
        konto_id INTEGER,
        type_id INTEGER,
        datum TEXT NOT NULL,
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (type_id) REFERENCES ausgabentypen(id)
    )
    """)

    # Kontostand
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kontostand (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        konto_id INTEGER NOT NULL,
        kontostand REAL NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (konto_id) REFERENCES konten(id)
    )
    """)

    # Depotbewegung
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS depotbewegung (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        konto_id INTEGER NOT NULL,
        aktien_id INTEGER NOT NULL,
        kategorie_id INTEGER,
        type_id INTEGER,
        betrag REAL NOT NULL,
        anteile REAL NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (aktien_id) REFERENCES wertpapierinfo(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (type_id) REFERENCES ausgabentypen(id)
    )
    """)

    # Depotstand
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS depotstand (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        konto_id INTEGER NOT NULL,
        aktien_id INTEGER NOT NULL,
        summe_betrag REAL NOT NULL,
        summe_anteil REAL NOT NULL,
        wert REAL NOT NULL,
        entwicklung REAL NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (aktien_id) REFERENCES wertpapierinfo(id)
    )
    """)

    # Sparziel
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS savings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ausgangs_konto_id INTEGER,
        kategorie_id INTEGER,
        betrag REAL, -- optional
        start_datum TEXT NOT NULL,
        next_due TEXT NOT NULL,
        Sparrate_e INTEGER,
        Sparrate_p INTEGER,
        Verwendungszweck TEXT NOT NULL,
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (ausgangs_konto_id) REFERENCES konten(id)
    )
    """)

    # Scheduler
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scheduler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        betrag REAL, -- optional
        anteil REAL, -- optional
        aktien_id INTEGER,
        kategorie_id INTEGER,
        ausgangs_konto_id INTEGER,
        eingangs_konto_id INTEGER,
        start_datum TEXT NOT NULL,
        next_due TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0,1)),
        FOREIGN KEY (aktien_id) REFERENCES wertpapierinfo(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (ausgangs_konto_id) REFERENCES konten(id),
        FOREIGN KEY (eingangs_konto_id) REFERENCES konten(id)
    )
    """)

    # Einkauf
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS einkauf (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        betrag REAL, -- optional
        kategorie_id INTEGER,
        konto_id INTEGER,
        laden_id INTEGER,
        ausgabentyp_id: INTEGER,
        datum TEXT NOT NULL,
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (laden_id) REFERENCES laden(id)
        FOREIGN KEY (ausgabentyp_id) REFERENCES ausgabentypen(id)
    )
    """)

    conn.commit()
    conn.close()
