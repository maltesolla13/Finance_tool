from Datenbank.DB_Config import get_connection
from GetData.GD_Schema import SchemaEinkauf, SchemaScheduler, \
    SchemaWertpapierInfo, SchemaAktienKurs, SchemaAusgabentyp, \
    SchemaDepotbewegung, SchemaDepotstand, SchemaKategorie, SchemaKonto, \
    SchemaKontobewegung, SchemaKontostand, SchemaLaden, SchemaSparziel


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

    def insert_wertpapierinfo(
            self,
            wertpapierinfo: SchemaWertpapierInfo
    ) -> SchemaWertpapierInfo:
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

    def update_wertpapierinfo(
            self,
            wertpapierinfo: SchemaWertpapierInfo
    ) -> None:
        """
       Aktualisiert einen bestehenden wertpapierinfo.

        Input
        -----
        wp

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE wertpapierinfo
            SET name = ?, isin = ?, ticker = ?, instrument = ?
            WHERE id = ?
        """, (
            wertpapierinfo["name"],
            wertpapierinfo["isin"],
            wertpapierinfo["ticker"],
            wertpapierinfo["instrument"],
            id
        ))

    def load_wertpapierinfo(self) -> list[SchemaWertpapierInfo]:
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
                            FROM wertpapierinfo")
        wertpapierinfo = self.cursor.fetchall()
        return wertpapierinfo

    def insert_kurs(self, kurs: SchemaAktienKurs) -> SchemaAktienKurs:
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
            Liste mit Tupeln (id, aktien_id, kurs, datum) des kurses
        """
        self.cursor.execute("SELECT id, aktien_id, kurs, datum FROM kurs")
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

    def load_kontobewegung(self) -> list[SchemaKontobewegung]:
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

    def insert_kontostand(
            self,
            kontostand: SchemaKontostand
    ) -> SchemaKontostand:
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

    def load_kontostand(self) -> list[SchemaKontostand]:
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

    def insert_depotbewegung(
            self,
            depotbewegung: SchemaDepotbewegung
    ) -> SchemaDepotbewegung:
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

    def load_depotbewegung(self) -> list[SchemaDepotbewegung]:
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

    def insert_depotstand(
            self,
            depotstand: SchemaDepotstand
    ) -> SchemaDepotstand:
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

    def load_depotstand(self) -> list[SchemaDepotstand]:
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

    def insert_scheduler(
            self,
            scheduler: SchemaScheduler
    ) -> SchemaScheduler:
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

    def load_scheduler(self) -> list[SchemaScheduler]:
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

    def update_scheduler(self, scheduler: SchemaScheduler) -> None:
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

    def insert_savings(
            self,
            savings: SchemaSparziel
    ) -> SchemaSparziel:
        """
        Fügt eine neue savings Eintrag in die Tabelle savings ein.

        Input
        -----
        savings: Ein Objekt mit Attribut
            'ausgangs_konto_id', 'kategorie_id', 'betrag', 'start_datum',
            'next_due', 'sparrate_e', 'sparrate_p', 'verwendungszweck'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO savings (ausgangs_konto_id, kategorie_id,  betrag,
                            start_datum, next_due, sparrate_e, sparrate_p,
                            verwendungszweck)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            savings.ausgangs_konto_id,
            savings.kategorie_id,
            savings.betrag,
            savings.start_datum,
            savings.next_due,
            savings.sparrate_e,
            savings.sparrate_p,
            savings.verwendungszweck
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
        List[Tuple[int, int, float, str, str, float, float, str]]
            Liste mit Tupeln (ausgangs_konto_id, kategorie_id,  betrag,
            start_datum, next_due, sparrate_e, sparrate_p,
            verwendungszweck) des savings
        """
        self.cursor.execute("SELECT ausgangs_konto_id, kategorie_id,  betrag,\
                            start_datum, next_due, sparrate_e, sparrate_p,\
                            verwendungszweck\
                            FROM savings")
        savings = self.cursor.fetchall()
        return savings

    def update_savings(self, savings: SchemaSparziel) -> None:
        """
        Aktualisiert einen bestehenden savings-Eintrag in der Tabelle
        savings.

        Input
        -----
        savings: Ein Objekt mit Attributen
            'ausgangs_konto_id', 'kategorie_id', 'betrag', 'start_datum',
            'next_due', 'sparrate_e', 'sparrate_p', 'verwendungszweck'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE savings
            SET ausgangs_konto_id = ?,
                kategorie_id = ?,
                betrag = ?,
                start_datum = ?,
                next_due = ?,
                sparrate_e = ?,
                sparrate_p = ?,
                verwendungszweck = ?
            WHERE id = ?
        """, (
            savings.ausgangs_konto_id,
            savings.kategorie_id,
            savings.betrag,
            savings.start_datum,
            savings.next_due,
            savings.sparrate_e,
            savings.sparrate_p,
            savings.verwendungszweck,
            savings.id
        ))

    def insert_einkauf(
            self,
            einkauf: SchemaEinkauf
    ) -> SchemaEinkauf:
        """
        Fügt eine neue einkauf Eintrag in die Tabelle einkauf ein.

        Input
        -----
        einkauf: Ein Objekt mit Attribut
            'name', 'betrag', 'kategorie_id', 'konto_id', 'laden_id',
            'ausgabentyp_id', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            INSERT INTO einkauf (name, betrag, kategorie_id, konto_id,
                            laden_id, ausgabentyp_id, datum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            einkauf.name,
            einkauf.betrag,
            einkauf.kategorie_id,
            einkauf.konto_id,
            einkauf.laden_id,
            einkauf.ausgabentyp_id,
            einkauf.datum
        ))

    def load_einkauf(self) -> list[SchemaEinkauf]:
        """
        Lädt alle Einträge aus der Tabelle einkauf und gibt diese als
        Liste von Tupeln zurück.

        Input
        -----
        None

        Response
        --------
        List[Tuple[str, float, int, int, int, int, str]]
            Liste mit Tupeln (name, betrag, kategorie_id, konto_id,
            laden_id, ausgabentyp_id, datum) des einkauf
        """
        self.cursor.execute("SELECT name, betrag,  kategorie_id,\
                            konto_id, laden_id, ausgabentyp_id, datum,\
                            FROM einkauf")
        einkauf = self.cursor.fetchall()
        return einkauf

    def update_einkauf(self, einkauf: SchemaEinkauf) -> None:
        """
        Aktualisiert einen bestehenden einkauf-Eintrag in der Tabelle
        einkauf.

        Input
        -----
        einkauf: Ein Objekt mit Attributen
            'name', 'betrag', 'kategorie_id', 'konto_id', 'laden_id',
            'ausgabentyp_id', 'datum'

        Response
        --------
        None
        """
        self.cursor.execute("""
            UPDATE einkauf
            SET name = ?,
                betrag = ?,
                kategorie_id = ?,
                konto_id = ?,
                laden_id = ?,
                ausgabentyp_id = ?,
                datum = ?
            WHERE id = ?
        """, (
            einkauf.name,
            einkauf.betrag,
            einkauf.kategorie_id,
            einkauf.konto_id,
            einkauf.laden_id,
            einkauf.ausgabentyp_id,
            einkauf.datum,
            einkauf.id
        ))
