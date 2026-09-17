from backend.app.database.db_config import get_connection
from backend.app.models.schema import SchemaReceipt, SchemaMonthlyCosts, \
    SchemaSecurities, SchemaAktienKurs, SchemaAusgabentyp, \
    SchemaDepotbewegung, SchemaDepotstand, SchemaKategorie, SchemaKonto, \
    SchemaKontobewegung, SchemaKontostand, SchemaLaden, SchemaSparziel, \
    SchemaUser, SchemaMonthlyCostsExecution
from decimal import Decimal
# from datetime import datetime


def _num(x):
    return float(x) if isinstance(x, Decimal) else x


def _dt(x):
    return x.isoformat() if hasattr(x, "isoformat") else x


class DBHandler:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def load_unique_names_from_db(self, table):
        """
        gibt eine sortierte Liste der Eindeutigen Namen zurück
        (wichtig für gui Comboxen)

        Input
        ----
        str
            sting mit Tabellennamen

        Response
        --------
        List
            Liste mit Namen aus Tabelle
        """
        self.cursor.execute(f"SELECT DISTINCT name FROM {table}")
        names = [row[0] for row in self.cursor.fetchall()]
        return sorted(names)

    def insert_laden(self, laden: SchemaLaden) -> SchemaLaden:
        """
        Fügt ein neuen Laden in die Tabelle laden ein.

        Input
        -----
        laden: Ein Objekt mit Attribut
            'name'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO laden (name)
            VALUES (?)
        """, (
            laden.name,
        ))

    def load_laden(self) -> list[SchemaLaden]:
        """
        Lädt alle Einträge aus der Tabelle laden und gibt diese als Liste von
        Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, str]]
            Liste mit Tupeln (id, name) der Läden
        """
        self.cursor.execute("SELECT id, name FROM laden")
        laden = self.cursor.fetchall()
        return laden

    def update_laden(self, laden: SchemaLaden) -> None:
        """
        Aktualisiert einen bestehenden Laden-Eintrag in der Tabelle laden.

        Input
        -----
        konto: Ein Objekt mit Attributen
            'id', 'name'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE laden
            SET name = ?
            WHERE id = ?
        """, (
            laden.name,
            laden.id
        ))

    def insert_user(self, user: SchemaUser) -> SchemaUser:
        """
        Fügt ein neuen User in die Tabelle user ein.

        Input
        -----
        user: Ein Objekt mit Attribut
            'name'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO user (name)
            VALUES (?)
        """, (
            user.name,
        ))

    def load_user(self) -> list[SchemaUser]:
        """
        Lädt alle Einträge aus der Tabelle user und gibt diese als Liste von
        Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, str]]
            Liste mit Tupeln (id, name) der User
        """
        self.cursor.execute("SELECT id, name FROM user")
        user = self.cursor.fetchall()
        return user

    def insert_konto(self, konto: SchemaKonto) -> SchemaKonto:
        """
        Fügt ein neues Konto in die Tabelle konten ein.

        Input
        -----
        konto: Ein Objekt mit Attribut
            'name'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO konten (name)
            VALUES (?)
        """, (
            konto.name,
        ))

    def load_konten(self) -> list[SchemaKonto]:
        """
        Lädt alle Einträge aus der Tabelle konten und gibt diese als Liste von
        Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, str]]
            Liste mit Tupeln (id, name) der Konten
        """
        self.cursor.execute("SELECT id, name FROM konten")
        konten = self.cursor.fetchall()
        return konten

    def update_konto(self, konto: SchemaKonto) -> None:
        """
        Aktualisiert einen bestehenden Konot-Eintrag in der Tabelle konten.

        Input
        -----
        konto: Ein Objekt mit Attributen
            'id', 'name'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE konten
            SET name = ?
            WHERE id = ?
        """, (
            konto.name,
            konto.id
        ))

    def insert_kategorie(self, kategorie: SchemaKategorie) -> SchemaKategorie:
        """
        Fügt eine neue Kategorie in die Tabelle kategorien ein.

        Input
        -----
        kategorie: Ein Objekt mit Attribut
            'name'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO kategorien (name)
            VALUES (?)
        """, (
            kategorie.name,
        ))

    def load_kategorien(self) -> list[SchemaKategorie]:
        """
        Lädt alle Einträge aus der Tabelle kategorien und gibt diese als Liste
        von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, str]]
            Liste mit Tupeln (id, name) der Kategorien
        """
        self.cursor.execute("SELECT id, name FROM kategorien")
        kategorien = self.cursor.fetchall()
        return kategorien

    def update_kategorie(self, kategorie: SchemaKategorie) -> None:
        """
        Aktualisiert einen bestehenden Konot-Eintrag in der Tabelle konten.

        Input
        -----
        kategorie: Ein Objekt mit Attributen
            'id', 'name'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE kategorien
            SET name = ?
            WHERE id = ?
        """, (
            kategorie.name,
            kategorie.id
        ))

    def insert_ausgabentyp(
            self,
            ausgabentyp: SchemaAusgabentyp
    ) -> SchemaAusgabentyp:
        """
        Fügt einen neuen Ausgabentyp in die Tabelle ausgabentypen ein.

        Input
        -----
        ausgabentyp: Ein Objekt mit Attribut
            'name'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO ausgabentypen (name)
            VALUES (?)
        """, (
            ausgabentyp.name,
        ))

    def load_ausgabentypen(self) -> list[SchemaAusgabentyp]:
        """
        Lädt alle Einträge aus der Tabelle ausgabentypen und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, str]]
            Liste mit Tupeln (id, name) der Ausgabentypen
        """
        self.cursor.execute("SELECT id, name FROM ausgabentypen")
        ausgabentypen = self.cursor.fetchall()
        return ausgabentypen

    def update_ausgabentyp(self, ausgabentyp: SchemaAusgabentyp) -> None:
        """
        Aktualisiert einen Ausgabentyp.
        """
        self.cursor.execute("""
            UPDATE ausgabentypen
            SET name = ?
            WHERE id = ?
        """, (ausgabentyp.name, ausgabentyp.id))
        self.conn.commit()

    def insert_securities(
            self,
            securities: SchemaSecurities
    ) -> SchemaSecurities:
        """
        Fügt eine neue Aktie in die Tabelle securities ein.

        Input
        -----
        Securities: Ein Objekt mit Attribut
            'name', 'isin', 'ticker', 'instrument'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO securities (name, isin, ticker, instrument)
            VALUES (?, ?, ?, ?)
        """, (
            securities.name,
            securities.isin,
            securities.ticker,
            securities.instrument
        ))

    def update_securities(
            self,
            securities: SchemaSecurities
    ) -> None:
        """
        Aktualisiert ein Wertpapier (name, isin, ticker, instrument).
        """
        self.cursor.execute("""
            UPDATE securities
            SET name = ?, isin = ?, ticker = ?, instrument = ?
            WHERE id = ?
        """, (
            securities.name,
            securities.isin,
            securities.ticker,
            securities.instrument,
            securities.id
        ))
        self.conn.commit()

    def load_securities(self) -> list[SchemaSecurities]:
        """
        Lädt alle Einträge aus der Tabelle securities und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, str, str, str, str]]
            Liste mit Tupeln (id, name, isin, ticker, instrument)
            der Securities
        """
        self.cursor.execute("SELECT id, name, isin, ticker, instrument\
                            FROM securities")
        securities = self.cursor.fetchall()
        return securities

    def insert_kurs(self, kurs: SchemaAktienKurs) -> SchemaAktienKurs:
        """
        Fügt eine neue Aktienstand in die Tabelle kurs ein.

        Input
        -----
        kurs: Ein Objekt mit Attribut
            'securities_id', 'kurs', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO kurs (securities_id, kurs, datum)
            VALUES (?, ?, ?)
        """, (
            kurs.securities_id,
            _num(kurs.kurs),
            _dt(kurs.datum)
        ))

    def load_kurs(self) -> list[SchemaAktienKurs]:
        """
        Lädt alle Einträge aus der Tabelle kurs und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, float, str]]
            Liste mit Tupeln (id, securities_id, kurs, datum) des kurses
        """
        self.cursor.execute("SELECT id, securities_id, kurs, datum FROM kurs")
        kurs = self.cursor.fetchall()
        return kurs

    def insert_kontobewegung(
            self,
            kontobewegung: SchemaKontobewegung
    ) -> SchemaKontobewegung:
        """
        Fügt ein neues Konto in die Tabelle konten ein.

        Input
        -----
        kontobewegung: Ein Objekt mit Attributen
            'user_id', 'name', 'betrag', 'kategorie_id', 'konto_id', 'type',
            'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO kontobewegung (
                    user_id, name, betrag, kategorie_id, konto_id, type,
                    datum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            kontobewegung.user_id,
            kontobewegung.name,
            _num(kontobewegung.betrag),
            kontobewegung.kategorie_id,
            kontobewegung.konto_id,
            kontobewegung.type,
            _dt(kontobewegung.datum)
        ))

    def load_kontobewegung(self) -> list[SchemaKontobewegung]:
        """
        Lädt alle Einträge aus der Tabelle kontobewegung und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, str, float, int, int, int, str]]
            Liste mit Tupeln (id, user_id, name, betrag, kategorie_id,
            konto_id, type, datum) der kontobewegung
        """
        self.cursor.execute("SELECT id, user_id, name, betrag, kategorie_id,\
                            konto_id, type, datum FROM kontobewegung")
        kontobewegung = self.cursor.fetchall()
        return kontobewegung

    def insert_kontostand(
            self,
            kontostand: SchemaKontostand
    ) -> SchemaKontostand:
        """
        Fügt eine neue Kontostand in die Tabelle kontostand ein.

        Input
        -----
        kontostand: Ein Objekt mit Attribut
            'user_id', 'konto_id', 'kontostand', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO kontostand (user_id, konto_id, kontostand, datum)
            VALUES (?, ?, ?, ?)
        """, (
            kontostand.user_id,
            kontostand.konto_id,
            _num(kontostand.kontostand),
            _dt(kontostand.datum)
        ))

    def load_kontostand(self) -> list[SchemaKontostand]:
        """
        Lädt alle Einträge aus der Tabelle kontostand und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, int, float, str]]
            Liste mit Tupeln (id, user_id, konto_id, kontostand, datum) des
            kontostand
        """
        self.cursor.execute("SELECT id, user_id, konto_id, kontostand, datum\
                            FROM kontostand")
        kontostand = self.cursor.fetchall()
        return kontostand

    def insert_depotbewegung(
            self,
            depotbewegung: SchemaDepotbewegung
    ) -> SchemaDepotbewegung:
        """
        Fügt eine neue Depotbewegung in die Tabelle depotbewegung ein.

        Input
        -----
        depotbewegung: Ein Objekt mit Attribut
            'user_id', 'konto_id', 'ausgangs_konto_id', 'eingangs_konto_id',
            'securities_id', 'kategorie_id', 'type', 'betrag', 'anteile',
            'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO depotbewegung (
                    user_id, konto_id, ausgangs_konto_id, eingangs_konto_id,
                    securities_id, kategorie_id, type, betrag, anteile,
                    datum, gebuehr)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            depotbewegung.user_id,
            depotbewegung.konto_id,
            getattr(depotbewegung, "ausgangs_konto_id", None),
            getattr(depotbewegung, "eingangs_konto_id", None),
            depotbewegung.securities_id,
            depotbewegung.kategorie_id,
            depotbewegung.type,
            _num(depotbewegung.betrag),
            _num(depotbewegung.anteile),
            _dt(depotbewegung.datum),
            _num(getattr(depotbewegung, "gebuehr", None) or 0),
        ))

    def load_depotbewegung(self) -> list[SchemaDepotbewegung]:
        """
        Lädt alle Einträge aus der Tabelle depotbewegung und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, int, int, int, int float, float, str]]
            Liste mit Tupeln (user_id, konto_id, ausgangs_konto_id,
                    eingangs_konto_id, securities_id, kategorie_id, type,
                    betrag, anteile, datum) des depotbewegung
        """
        self.cursor.execute("SELECT id, user_id, konto_id,\
                            ausgangs_konto_id, eingangs_konto_id,\
                            securities_id, kategorie_id, type, betrag,\
                            anteile, datum, gebuehr FROM depotbewegung")
        depotbewegung = self.cursor.fetchall()
        return depotbewegung

    def update_depotbewegung(
            self,
            depotbewegung: SchemaDepotbewegung
    ) -> None:
        self.cursor.execute("""
            UPDATE depotbewegung
            SET user_id = ?,
                konto_id = ?,
                ausgangs_konto_id = ?,
                eingangs_konto_id = ?,
                securities_id = ?,
                kategorie_id = ?,
                type = ?,
                betrag = ?,
                anteile = ?,
                datum = ?,
                gebuehr = ?
            WHERE id = ?
        """, (
            depotbewegung.user_id,
            depotbewegung.konto_id,
            getattr(depotbewegung, "ausgangs_konto_id", None),
            getattr(depotbewegung, "eingangs_konto_id", None),
            depotbewegung.securities_id,
            depotbewegung.kategorie_id,
            depotbewegung.type,
            _num(depotbewegung.betrag),
            _num(depotbewegung.anteile),
            _dt(depotbewegung.datum),
            _num(getattr(depotbewegung, "gebuehr", None) or 0),
            depotbewegung.id,
        ))

    def insert_depotstand(
            self,
            depotstand: SchemaDepotstand
    ) -> SchemaDepotstand:
        """
        Fügt eine neue depotstand in die Tabelle depotstand ein.

        Input
        -----
        depotstand: Ein Objekt mit Attribut
            'user_id', 'konto_id', 'securities_id', 'summe_betrag',
            'summe_anteil', 'wert', 'entwicklung', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO depotstand (user_id, konto_id, securities_id,\
                            summe_betrag, summe_anteil, wert, entwicklung,\
                            datum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            depotstand.user_id,
            depotstand.konto_id,
            depotstand.securities_id,
            _num(depotstand.summe_betrag),
            _num(depotstand.summe_anteil),
            _num(depotstand.wert),
            _num(depotstand.entwicklung),
            _dt(depotstand.datum)
        ))

    def load_depotstand(self) -> list[SchemaDepotstand]:
        """
        Lädt alle Einträge aus der Tabelle depotstand und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, int, int, float, float, float, float, str]]
            Liste mit Tupeln (id, user_id, konto_id, securities_id,
            summe_betrag, summe_anteil, wert, entwicklung, datum)
            des depotstand
        """
        self.cursor.execute("SELECT id, user_id, konto_id, securities_id,\
                            summe_betrag, summe_anteil, wert, entwicklung,\
                             datum FROM depotstand")
        depotstand = self.cursor.fetchall()
        return depotstand

    def insert_monthlycosts(
            self,
            monthlycosts: SchemaMonthlyCosts
    ) -> SchemaMonthlyCosts:
        """
        Fügt eine neue monthlycosts Eintrag in die Tabelle monthlycosts ein.

        Input
        -----
        monthlycosts: Ein Objekt mit Attribut
            'user_id', 'name', 'betrag', 'anteil', 'securities_id',
            'kategorie_id', 'ausgangs_konto_id', 'eingangs_konto_id',
            'start_datum', 'next_due', 'repeat_type', 'custom_interval',
            'custom_unit', 'active'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO monthlycosts (user_id, name, betrag, anteil,
                            securities_id, kategorie_id, ausgangs_konto_id,
                            eingangs_konto_id, start_datum, next_due,
                            repeat_type, custom_interval, custom_unit, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            monthlycosts.user_id,
            monthlycosts.name,
            _num(monthlycosts.betrag),
            _num(monthlycosts.anteil),
            monthlycosts.securities_id,
            monthlycosts.kategorie_id,
            monthlycosts.ausgangs_konto_id,
            monthlycosts.eingangs_konto_id,
            _dt(monthlycosts.start_datum),
            _dt(monthlycosts.next_due),
            monthlycosts.repeat_type,
            monthlycosts.custom_interval,
            monthlycosts.custom_unit,
            monthlycosts.active
        ))

    def load_monthlycosts(self) -> list[SchemaMonthlyCosts]:
        """
        Lädt alle Einträge aus der Tabelle monthlycosts und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, int, int, float, float, float, float, str]]
            Liste mit Tupeln (id, user_id, name, betrag, anteil, securities_id,
            kategorie_id, ausgangs_konto_id, eingangs_konto_id, start_datum,
            next_due, repeat_type, custom_interval, custom_unit, active)
            des monthlycosts
        """
        self.cursor.execute("SELECT id, user_id, name, betrag, anteil,\
                            securities_id, kategorie_id, ausgangs_konto_id,\
                            eingangs_konto_id, start_datum, next_due,\
                            repeat_type, custom_interval, custom_unit, active\
                            FROM monthlycosts")
        monthlycosts = self.cursor.fetchall()
        return monthlycosts

    def update_monthlycosts(self, monthlycosts: SchemaMonthlyCosts) -> None:
        """
        Aktualisiert einen bestehenden monthlycosts-Eintrag in der Tabelle
        monthlycosts.

        Input
        -----
        monthlycosts: Ein Objekt mit Attributen
            'id', 'user_id', 'name', 'betrag', 'anteil', 'securities_id',
            'kategorie_id', 'ausgangs_konto_id', 'eingangs_konto_id',
            'start_datum', 'next_due', 'repeat_type', 'custom_interval',
            'custom_unit', 'active'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE monthlycosts
            SET user_id = ?,
                name = ?,
                betrag = ?,
                anteil = ?,
                securities_id = ?,
                kategorie_id = ?,
                ausgangs_konto_id = ?,
                eingangs_konto_id = ?,
                start_datum = ?,
                next_due = ?,
                repeat_type = ?,
                custom_interval = ?,
                custom_unit = ?,
                active = ?
            WHERE id = ?
        """, (
            monthlycosts.user_id,
            monthlycosts.name,
            _num(monthlycosts.betrag),
            _num(monthlycosts.anteil),
            monthlycosts.securities_id,
            monthlycosts.kategorie_id,
            monthlycosts.ausgangs_konto_id,
            monthlycosts.eingangs_konto_id,
            _dt(monthlycosts.start_datum),
            _dt(monthlycosts.next_due),
            monthlycosts.repeat_type,
            monthlycosts.custom_interval,
            monthlycosts.custom_unit,
            monthlycosts.active,
            monthlycosts.id
        ))

    def insert_monthlycosts_execution(
            self,
            execution: SchemaMonthlyCostsExecution
    ) -> SchemaMonthlyCostsExecution:
        self.cursor.execute("""
            INSERT INTO monthlycosts_execution (
                monthlycost_id, user_id, name, betrag, anteil, securities_id,
                kategorie_id, ausgangs_konto_id, eingangs_konto_id,
                execution_datum, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution.monthlycost_id,
            execution.user_id,
            execution.name,
            _num(execution.betrag),
            _num(execution.anteil),
            execution.securities_id,
            execution.kategorie_id,
            execution.ausgangs_konto_id,
            execution.eingangs_konto_id,
            _dt(execution.execution_datum),
            execution.status,
        ))

    def load_monthlycosts_execution(
            self) -> list[SchemaMonthlyCostsExecution]:
        self.cursor.execute("""
            SELECT id, monthlycost_id, user_id, name, betrag, anteil,
                   securities_id, kategorie_id, ausgangs_konto_id,
                   eingangs_konto_id, execution_datum, status
            FROM monthlycosts_execution
        """)
        return self.cursor.fetchall()

    def update_monthlycosts_execution(
            self,
            execution: SchemaMonthlyCostsExecution
    ) -> None:
        self.cursor.execute("""
            UPDATE monthlycosts_execution
            SET monthlycost_id = ?,
                user_id = ?,
                name = ?,
                betrag = ?,
                anteil = ?,
                securities_id = ?,
                kategorie_id = ?,
                ausgangs_konto_id = ?,
                eingangs_konto_id = ?,
                execution_datum = ?,
                status = ?
            WHERE id = ?
        """, (
            execution.monthlycost_id,
            execution.user_id,
            execution.name,
            _num(execution.betrag),
            _num(execution.anteil),
            execution.securities_id,
            execution.kategorie_id,
            execution.ausgangs_konto_id,
            execution.eingangs_konto_id,
            _dt(execution.execution_datum),
            execution.status,
            execution.id,
        ))

    def insert_savings(
            self,
            savings: SchemaSparziel
    ) -> SchemaSparziel:
        """
        Fügt eine neue savings Eintrag in die Tabelle savings ein.

        Input
        -----
        savings: Ein Objekt mit Attribut
            'name', 'user_id', 'konto_id', 'kategorie_id', 'betrag',
            'start_datum', 'end_datum', 'sparrate_e', 'sparrate_p'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO savings (name, user_id, konto_id, kategorie_id,
                            betrag, start_datum, end_datum, sparrate_e,
                            sparrate_p)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            savings.name,
            savings.user_id,
            savings.konto_id,
            savings.kategorie_id,
            _num(savings.betrag),
            _dt(savings.start_datum),
            _dt(savings.end_datum),
            _num(savings.sparrate_e),
            _num(savings.sparrate_p)
        ))

    def load_savings(self) -> list[SchemaSparziel]:
        """
        Lädt alle Einträge aus der Tabelle savings und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[str, int, int, int, float, str, str, float, float]]
            Liste mit Tupeln (user_id, konto_id, kategorie_id, betrag,
            start_datum, end_datum, sparrate_e, sparrate_p,) des savings
        """
        self.cursor.execute("SELECT id, name, user_id, konto_id, kategorie_id,\
                            betrag, start_datum, end_datum, sparrate_e,\
                            sparrate_p FROM savings")
        savings = self.cursor.fetchall()
        return savings

    def update_savings(self, savings: SchemaSparziel) -> None:
        """
        Aktualisiert einen bestehenden savings-Eintrag in der Tabelle
        savings.

        Input
        -----
        savings: Ein Objekt mit Attributen
            'name', 'user_id', 'konto_id', 'kategorie_id', 'betrag',
            'start_datum', 'end_datum', 'sparrate_e', 'sparrate_p'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE savings
            SET name = ?,
                user_id = ?,
                konto_id = ?,
                kategorie_id = ?,
                betrag = ?,
                start_datum = ?,
                end_datum = ?,
                sparrate_e = ?,
                sparrate_p = ?
            WHERE id = ?
        """, (
            savings.name,
            savings.user_id,
            savings.konto_id,
            savings.kategorie_id,
            _num(savings.betrag),
            _dt(savings.start_datum),
            _dt(savings.end_datum),
            _num(savings.sparrate_e),
            _num(savings.sparrate_p),
            savings.id
        ))

    def insert_receipt(
            self,
            receipt: SchemaReceipt
    ) -> SchemaReceipt:
        """
        Fügt eine neue receipt Eintrag in die Tabelle receipt ein.

        Input
        -----
        receipt: Ein Objekt mit Attribut
            'user_id', 'name', 'betrag', 'kategorie_id', 'konto_id',
            'laden_id', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO receipt (user_id, name, betrag, kategorie_id, konto_id,
                            laden_id, datum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            receipt.user_id,
            receipt.name,
            _num(receipt.betrag),
            receipt.kategorie_id,
            receipt.konto_id,
            receipt.laden_id,
            _dt(receipt.datum)
        ))

    def load_receipt(self) -> list[tuple]:
        """
        Lädt alle Einkäufe.
        Rückgabe: Liste von Tupeln (id, user_id, name, betrag, kategorie_id,
        konto_id, laden_id,  datum)
        """
        self.cursor.execute("""
            SELECT id, user_id, name, betrag, kategorie_id, konto_id, laden_id,
                             datum
            FROM receipt
        """)
        return self.cursor.fetchall()

    def update_receipt(self, receipt: SchemaReceipt) -> None:
        """
        Aktualisiert einen bestehenden receipt-Eintrag in der Tabelle
        receipt.

        Input
        -----
        receipt: Ein Objekt mit Attributen
            'user_id', 'name', 'betrag', 'kategorie_id', 'konto_id',
            'laden_id', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE receipt
            SET user_id = ?,
                name = ?,
                betrag = ?,
                kategorie_id = ?,
                konto_id = ?,
                laden_id = ?,
                datum = ?
            WHERE id = ?
        """, (
            receipt.user_id,
            receipt.name,
            _num(receipt.betrag),
            receipt.kategorie_id,
            receipt.konto_id,
            receipt.laden_id,
            _dt(receipt.datum),
            receipt.id
        ))
