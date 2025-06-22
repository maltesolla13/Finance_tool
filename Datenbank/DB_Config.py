import os
import sqlite3


def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "finance_tracker.db")
    conn = sqlite3.connect(db_path)
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

    # AktienInfo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aktieninfo (
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
        FOREIGN KEY (aktien_id) REFERENCES aktieninfo(id)
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
        FOREIGN KEY (aktien_id) REFERENCES aktieninfo(id),
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
        FOREIGN KEY (aktien_id) REFERENCES aktieninfo(id)
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
        start_datum TEXT NOT NULL
        next_due TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0,1)),
        FOREIGN KEY (aktien_id) REFERENCES aktieninfo(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (ausgangs_konto_id) REFERENCES konten(id),
        FOREIGN KEY (eingangs_konto_id) REFERENCES konten(id)
    )
    """)

    conn.commit()
    conn.close()
