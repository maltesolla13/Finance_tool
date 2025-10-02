from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SchemaKonto:
    id: Optional[int] = None
    name: str


@dataclass
class SchemaUser:
    id: Optional[int] = None
    name: str


@dataclass
class SchemaKategorie:
    id: Optional[int] = None
    name: str


@dataclass
class SchemaAusgabentyp:
    id: Optional[int] = None
    name: str


@dataclass
class SchemaLaden:
    id: Optional[int] = None
    name: str


@dataclass
class SchemaWertpapierInfo:
    id:    Optional[int] = None
    name: str
    isin: str
    ticker: str  # (stock, etf, crypto)
    instrument: str


@dataclass
class SchemaAktienKurs:
    id: Optional[int] = None
    aktien_id: int
    kurs: Decimal
    datum: datetime


@dataclass
class SchemaKontobewegung:
    id: Optional[int] = None
    user_id: int
    name: str
    betrag: Decimal
    kategorie_id: int
    konto_id: int
    type_id: int
    datum: datetime


@dataclass
class SchemaKontostand:
    id: Optional[int] = None
    user_id: int
    konto_id: int
    kontostand: Decimal
    datum: datetime


@dataclass
class SchemaDepotbewegung:
    id: Optional[int] = None
    user_id: int
    konto_id: int
    aktien_id: int
    kategorie_id: int
    type_id: int
    betrag: Decimal
    anteile: Decimal
    datum: datetime


@dataclass
class SchemaDepotstand:
    id: Optional[int] = None
    user_id: int
    konto_id: int
    aktien_id: int
    summe_betrag: Decimal
    summe_anteil: Decimal
    wert: Decimal
    entwicklung: Decimal
    datum: datetime


@dataclass
class SchemaSparziel:
    id: Optional[int] = None
    user_id: int
    ausgangs_konto_id: int
    kategorie_id: int
    betrag: Decimal
    start_datum: datetime
    next_due: datetime
    sparrate_e: Decimal
    sparrate_p: Decimal
    verwendungszweck: str


@dataclass
class SchemaScheduler:
    id: Optional[int] = None
    user_id: int
    name: str
    kategorie_id: int
    start_datum: datetime
    next_due: datetime
    active: bool
    ausgangs_konto_id: Optional[int] = None
    eingangs_konto_id: Optional[int] = None
    aktien_id: Optional[int] = None
    anteil: Optional[Decimal] = None
    betrag: Optional[Decimal] = None


@dataclass
class SchemaEinkauf:
    id: Optional[int] = None
    user_id: int
    name: str
    betrag: Decimal
    kategorie_id: int
    konto_id: int
    laden_id: int
    ausgabentyp_id: int
    datum: datetime
