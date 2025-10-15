import sqlite3
from pathlib import Path


base_dir = Path(__file__).resolve().parent.parent.parent
db_path = base_dir / "data" / "finance_tracker.db"


def get_connection():
    db_path.parent.mkdir(parents=True, exist_ok=True)
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
        name TEXT NOT NULL UNIQUE
    )
    """)

    # Nutzer
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    # Kategorien
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kategorien (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    # AusgabenTypen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ausgabentypen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    # Laden
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS laden (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    # Securities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS securities (
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
        securities_id INTEGER NOT NULL,
        kurs REAL NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (securities_id) REFERENCES securities(id)
    )
    """)

    # Kontobewegung
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kontobewegung (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        betrag REAL NOT NULL,
        kategorie_id INTEGER,
        konto_id INTEGER,
        type_id INTEGER,
        datum TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (type_id) REFERENCES ausgabentypen(id)
    )
    """)

    # Kontostand
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kontostand (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        konto_id INTEGER NOT NULL,
        kontostand REAL NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id)
    )
    """)

    # Depotbewegung
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS depotbewegung (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        konto_id INTEGER NOT NULL,
        securities_id INTEGER NOT NULL,
        kategorie_id INTEGER,
        type_id INTEGER,
        betrag REAL NOT NULL,
        anteile REAL NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (securities_id) REFERENCES securities(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (type_id) REFERENCES ausgabentypen(id)
    )
    """)

    # Depotstand
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS depotstand (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        konto_id INTEGER NOT NULL,
        securities_id INTEGER NOT NULL,
        summe_betrag REAL NOT NULL,
        summe_anteil REAL NOT NULL,
        wert REAL NOT NULL,
        entwicklung REAL NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (securities_id) REFERENCES securities(id)
    )
    """)

    # Sparziel
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS savings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        user_id INTEGER,
        konto_id INTEGER,
        kategorie_id INTEGER,
        betrag REAL, -- optional
        start_datum TEXT NOT NULL,
        end_datum TEXT NOT NULL,
        sparrate_e INTEGER,
        sparrate_p INTEGER,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id)
    )
    """)

    # MonthlyCosts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monthlycosts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        betrag REAL, -- optional
        anteil REAL, -- optional
        securities_id INTEGER,
        kategorie_id INTEGER,
        ausgangs_konto_id INTEGER,
        eingangs_konto_id INTEGER,
        start_datum TEXT NOT NULL,
        next_due TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0,1)),
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (securities_id) REFERENCES securities(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (ausgangs_konto_id) REFERENCES konten(id),
        FOREIGN KEY (eingangs_konto_id) REFERENCES konten(id)
    )
    """)

    # Receipt
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receipt (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        betrag REAL, -- optional
        kategorie_id INTEGER,
        konto_id INTEGER,
        laden_id INTEGER,
        datum TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (laden_id) REFERENCES laden(id)
    )
    """)

    conn.commit()
    conn.close()
