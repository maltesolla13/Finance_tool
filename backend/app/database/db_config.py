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
        type TEXT NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id)
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
        ausgangs_konto_id INTEGER,
        eingangs_konto_id INTEGER,
        securities_id INTEGER NOT NULL,
        kategorie_id INTEGER,
        type TEXT NOT NULL,
        betrag REAL NOT NULL,
        anteile REAL NOT NULL,
        datum TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (ausgangs_konto_id) REFERENCES konten(id),
        FOREIGN KEY (eingangs_konto_id) REFERENCES konten(id),
        FOREIGN KEY (securities_id) REFERENCES securities(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id)
    )
    """)
    depotbewegung_cols = {
        row[1]: row for row in cursor.execute("PRAGMA table_info(depotbewegung)")
    }
    if "ausgangs_konto_id" not in depotbewegung_cols:
        cursor.execute(
            "ALTER TABLE depotbewegung ADD COLUMN ausgangs_konto_id INTEGER"
        )
    if "eingangs_konto_id" not in depotbewegung_cols:
        cursor.execute(
            "ALTER TABLE depotbewegung ADD COLUMN eingangs_konto_id INTEGER"
        )
    cursor.execute("""
        UPDATE depotbewegung
        SET ausgangs_konto_id = COALESCE(ausgangs_konto_id, konto_id),
            eingangs_konto_id = COALESCE(eingangs_konto_id, konto_id)
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

    savings_cols = {
        row[1]: row for row in cursor.execute("PRAGMA table_info(savings)")
    }
    if savings_cols.get("end_datum") and savings_cols["end_datum"][3]:
        cursor.execute("ALTER TABLE savings RENAME TO savings_old")
        cursor.execute("""
        CREATE TABLE savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER,
            konto_id INTEGER,
            kategorie_id INTEGER,
            betrag REAL,
            start_datum TEXT NOT NULL,
            end_datum TEXT,
            sparrate_e REAL,
            sparrate_p REAL,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
            FOREIGN KEY (konto_id) REFERENCES konten(id)
        )
        """)
        cursor.execute("""
        INSERT INTO savings (
            id, name, user_id, konto_id, kategorie_id, betrag, start_datum,
            end_datum, sparrate_e, sparrate_p)
        SELECT id, name, user_id, konto_id, kategorie_id, betrag, start_datum,
               end_datum, sparrate_e, sparrate_p
        FROM savings_old
        """)
        cursor.execute("DROP TABLE savings_old")

    # SavingsExecution
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS savings_execution (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        savings_id INTEGER NOT NULL,
        user_id INTEGER,
        konto_id INTEGER,
        kategorie_id INTEGER,
        income_kontobewegung_id INTEGER,
        execution_month TEXT NOT NULL,
        income_amount REAL,
        amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'EXECUTED',
        FOREIGN KEY (savings_id) REFERENCES savings(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (konto_id) REFERENCES konten(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (income_kontobewegung_id) REFERENCES kontobewegung(id),
        CHECK (status IN ('EXECUTED', 'SKIPPED'))
    )
    """)

    # MonthlyCosts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monthlycosts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        betrag REAL, -- optional
        anteil REAL, -- optional
        securities_id INTEGER,
        kategorie_id INTEGER,
        ausgangs_konto_id INTEGER,
        eingangs_konto_id INTEGER,
        start_datum TEXT NOT NULL,
        next_due TEXT,
        repeat_type TEXT NOT NULL DEFAULT 'MONTHLY',
        custom_interval INTEGER,
        custom_unit TEXT,
        active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (securities_id) REFERENCES securities(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (ausgangs_konto_id) REFERENCES konten(id),
        FOREIGN KEY (eingangs_konto_id) REFERENCES konten(id),

        CHECK (repeat_type IN (
                   'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY', 'CUSTOM')),
        CHECK (custom_unit IS NULL OR custom_unit IN (
                   'DAYS', 'WEEKS', 'MONTHS', 'YEARS')),
        CHECK (custom_interval IS NULL OR custom_interval > 0),
        CHECK (
            repeat_type != 'CUSTOM'
            OR (
                custom_interval IS NOT NULL
                AND custom_interval > 0
                AND custom_unit IS NOT NULL
            )
        )
    )
    """)

    # MonthlyCostsExecution
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monthlycosts_execution (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monthlycost_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        betrag REAL, -- optional
        anteil REAL, -- optional
        securities_id INTEGER,
        kategorie_id INTEGER,
        ausgangs_konto_id INTEGER,
        eingangs_konto_id INTEGER,
        execution_datum TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        FOREIGN KEY (monthlycost_id) REFERENCES monthlycosts(id),
        FOREIGN KEY (user_id) REFERENCES user(id),
        FOREIGN KEY (securities_id) REFERENCES securities(id),
        FOREIGN KEY (kategorie_id) REFERENCES kategorien(id),
        FOREIGN KEY (ausgangs_konto_id) REFERENCES konten(id),
        FOREIGN KEY (eingangs_konto_id) REFERENCES konten(id),
        CHECK (status IN ('PENDING', 'EXECUTED', 'FAILED', 'SKIPPED'))
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

    from backend.app.services.account_users import init_account_users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS depot_sparplan_execution (
            monthlycost_id INTEGER NOT NULL REFERENCES monthlycosts(id) ON DELETE CASCADE,
            datum TEXT NOT NULL,
            depotbewegung_id INTEGER NOT NULL UNIQUE REFERENCES depotbewegung(id) ON DELETE CASCADE,
            PRIMARY KEY (monthlycost_id, datum)
        )
    """)
    init_account_users(conn)
    conn.commit()
    conn.close()
