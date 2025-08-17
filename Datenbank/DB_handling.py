from Datenbank.DB_Config import get_connection
from GetData.GD_Schema import SchemaEinkauf, SchemaScheduler, \
    SchemaWertpapierInfo, SchemaAktienKurs, SchemaAusgabentyp, \
    SchemaDepotbewegung, SchemaDepotstand, SchemaKategorie, SchemaKonto, \
    SchemaKontobewegung, SchemaKontostand, SchemaLaden


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

    def insert_ausgabentyp(self, ausgabentyp: SchemaAusgabentyp) -> SchemaAusgabentyp:
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
        Aktualisiert einen bestehenden Konot-Eintrag in der Tabelle konten.

        Input
        -----
        ausgabentyp: Ein Objekt mit Attributen
            'id', 'name'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE ausgabentyp
            SET name = ?
            WHERE id = ?
        """, (
            ausgabentyp.name,
            ausgabentyp.id
        ))

    def insert_wertpapierinfo(self, wertpapierinfo: SchemaWertpapierInfo) -> SchemaWertpapierInfo:
        """
        Fügt eine neue Aktie in die Tabelle wertpapierinfo ein.

        Input
        -----
        aktieninfo: Ein Objekt mit Attribut
            'name', 'isin', 'ticker', 'instrument'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO wertpapierinfo (name, isin, ticker, instrument)
            VALUES (?, ?, ?, ?)
        """, (
            wertpapierinfo.name,
            wertpapierinfo.isin,
            wertpapierinfo.ticker,
            wertpapierinfo.instrument
        ))

    def update_wertpapierinfo(self, wertpapierinfo, id):
        """
       Aktualisiert einen bestehenden Aktieneintrag.

        Input
        -----
        wp

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE aktieninfo
            SET name = ?, isin = ?, ticker = ?, instrument = ?
            WHERE id = ?
        """, (
            wertpapierinfo["name"],
            wertpapierinfo["isin"],
            wertpapierinfo["ticker"],
            wertpapierinfo["instrument"],
            id
        ))

    def load_wertpapierinfo(self):
        """
        Lädt alle Einträge aus der Tabelle wertpapierinfo und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, str, str, str, str]]
            Liste mit Tupeln (id, name, isin, ticker, instrument)
            der aktieninfo
        """
        self.cursor.execute("SELECT id, name, isin, ticker, instrument\
                            FROM aktieninfo")
        aktieninfo = self.cursor.fetchall()
        return aktieninfo

    def insert_kurs(self, kurs):
        """
        Fügt eine neue Aktienstand in die Tabelle kurs ein.

        Input
        -----
        kurs: Ein Objekt mit Attribut
            'aktien_id', 'kurs', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO kurs (aktien_id, kurs, datum)
            VALUES (?, ?, ?)
        """, (
            kurs.aktien_id,
            kurs.kurs,
            kurs.datum
        ))

    def load_kurs(self):
        """
        Lädt alle Einträge aus der Tabelle kurs und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, float, str]]
            Liste mit Tupeln (id, aktien_id, kurs, datum) des kurses
        """
        self.cursor.execute("SELECT id, aktien_id, kurs, datum FROM kurs")
        kurs = self.cursor.fetchall()
        return kurs

    def insert_kontobewegung(self, kontobewegung):
        """
        Fügt ein neues Konto in die Tabelle konten ein.

        Input
        -----
        kontobewegung: Ein Objekt mit Attributen
            'name', 'betrag', 'kategorie_id', 'konto_id', 'type_id', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO kontobewegung (
                    name, betrag, kategorie_id, konto_id, type_id, datum)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            kontobewegung.name,
            kontobewegung.betrag,
            kontobewegung.kategorie_id,
            kontobewegung.konto_id,
            kontobewegung.type_id,
            kontobewegung.datum
        ))

    def load_kontobewegung(self):
        """
        Lädt alle Einträge aus der Tabelle kontobewegung und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, str, float, int, int, int, str]]
            Liste mit Tupeln (id, name, betrag, kategorie_id, konto_id,
            type_id, datum) der kontobewegung
        """
        self.cursor.execute("SELECT id, name, betrag, kategorie_id, konto_id,\
                            type_id, datum FROM kontobewegung")
        kontobewegung = self.cursor.fetchall()
        return kontobewegung

    def insert_kontostand(self, kontostand):
        """
        Fügt eine neue Kontostand in die Tabelle kontostand ein.

        Input
        -----
        kontostand: Ein Objekt mit Attribut
            'konto_id', 'kontostand', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO kontostand (konto_id, kontostand, datum)
            VALUES (?, ?, ?)
        """, (
            kontostand.konto_id,
            kontostand.kontostand,
            kontostand.datum
        ))

    def load_kontostand(self):
        """
        Lädt alle Einträge aus der Tabelle kontostand und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, float, str]]
            Liste mit Tupeln (id, konto_id, kontostand, datum) des kontostand
        """
        self.cursor.execute("SELECT id, konto_id, kontostand, datum\
                            FROM kontostand")
        kontostand = self.cursor.fetchall()
        return kontostand

    def insert_depotbewegung(self, depotbewegung):
        """
        Fügt eine neue Depotbewegung in die Tabelle depotbewegung ein.

        Input
        -----
        depotbewegung: Ein Objekt mit Attribut
            'konto_id', 'aktien_id', 'kategorie_id', 'type_id', 'betrag',
            'anteile', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO depotbewegung (konto_id, aktien_id, kategorie_id,
                    type_id, betrag, anteile, datum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            depotbewegung.konto_id,
            depotbewegung.aktien_id,
            depotbewegung.kategorie_id,
            depotbewegung.type_id,
            depotbewegung.betrag,
            depotbewegung.anteile,
            depotbewegung.datum
        ))

    def load_depotbewegung(self):
        """
        Lädt alle Einträge aus der Tabelle depotbewegung und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, int, int, int float, float, str]]
            Liste mit Tupeln (konto_id, aktien_id, kategorie_id,
                    type_id, betrag, anteile, datum) des depotbewegung
        """
        self.cursor.execute("SELECT id, konto_id, aktien_id, kategorie_id,\
                    type_id, betrag, anteile, datum FROM depotbewegung")
        depotbewegung = self.cursor.fetchall()
        return depotbewegung

    def insert_depotstand(self, depotstand):
        """
        Fügt eine neue depotstand in die Tabelle depotstand ein.

        Input
        -----
        depotstand: Ein Objekt mit Attribut
            'konto_id', 'aktien_id', 'summe_betrag', 'summe_anteil',
             'wert', 'entwicklung', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO depotstand (konto_id, aktien_id, summe_betrag,\
                            summe_anteil, wert, entwicklung, datum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            depotstand.konto_id,
            depotstand.aktien_id,
            depotstand.summe_betrag,
            depotstand.summe_anteil,
            depotstand.wert,
            depotstand.entwicklung,
            depotstand.datum
        ))

    def load_depotstand(self):
        """
        Lädt alle Einträge aus der Tabelle depotstand und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, int, float, float, float, float, str]]
            Liste mit Tupeln (id, konto_id, aktien_id, summe_betrag,
            summe_anteil, wert, entwicklung, datum) des depotstand
        """
        self.cursor.execute("SELECT id, konto_id, aktien_id, summe_betrag,\
                            summe_anteil, wert, entwicklung, datum\
                            FROM depotstand")
        depotstand = self.cursor.fetchall()
        return depotstand

    def insert_scheduler(self, scheduler):
        """
        Fügt eine neue scheduler Eintrag in die Tabelle scheduler ein.

        Input
        -----
        scheduler: Ein Objekt mit Attribut
            'name', 'betrag', 'anteil', 'aktien_id', 'kategorie_id',
            'ausgangs_konto_id', 'eingangs_konto_id', 'start_datum',
            'next_due', 'active'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO scheduler (name, betrag, anteil, aktien_id,
                            kategorie_id, ausgangs_konto_id,
                            eingangs_konto_id,start_datum, next_due, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scheduler.name,
            scheduler.betrag,
            scheduler.anteil,
            scheduler.aktien_id,
            scheduler.kategorie_id,
            scheduler.ausgangs_konto_id,
            scheduler.eingangs_konto_id,
            scheduler.start_datum,
            scheduler.next_due,
            scheduler.active
        ))

    def load_scheduler(self):
        """
        Lädt alle Einträge aus der Tabelle scheduler und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[int, int, int, float, float, float, float, str]]
            Liste mit Tupeln (id, name, betrag, anteil, aktien_id,
            kategorie_id, ausgangs_konto_id, eingangs_konto_id, start_datum,
            next_due, active) des scheduler
        """
        self.cursor.execute("SELECT id, name, betrag, anteil, aktien_id,\
                            kategorie_id, ausgangs_konto_id,\
                            eingangs_konto_id, start_datum, next_due, active\
                            FROM scheduler")
        scheduler = self.cursor.fetchall()
        return scheduler

    def update_scheduler(self, scheduler):
        """
        Aktualisiert einen bestehenden Scheduler-Eintrag in der Tabelle
        scheduler.

        Input
        -----
        scheduler: Ein Objekt mit Attributen
            'id', 'name', 'betrag', 'anteil', 'aktien_id', 'kategorie_id',
            'ausgangs_konto_id', 'eingangs_konto_id', 'start_datum',
            'next_due', 'active'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE scheduler
            SET name = ?,
                betrag = ?,
                anteil = ?,
                aktien_id = ?,
                kategorie_id = ?,
                ausgangs_konto_id = ?,
                eingangs_konto_id = ?,
                start_datum = ?,
                next_due = ?,
                active = ?
            WHERE id = ?
        """, (
            scheduler.name,
            scheduler.betrag,
            scheduler.anteil,
            scheduler.aktien_id,
            scheduler.kategorie_id,
            scheduler.ausgangs_konto_id,
            scheduler.eingangs_konto_id,
            scheduler.start_datum,
            scheduler.next_due,
            scheduler.active,
            scheduler.id
        ))
