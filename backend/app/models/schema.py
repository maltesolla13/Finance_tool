from decimal import Decimal
from pydantic.dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SchemaOption:
    id: int
    name: str


@dataclass
class SchemaKonto:
    name: str
    id: Optional[int] = None


@dataclass
class SchemaUser:
    name: str
    id: Optional[int] = None


@dataclass
class SchemaKategorie:
    name: str
    id: Optional[int] = None


@dataclass
class SchemaAusgabentyp:
    name: str
    id: Optional[int] = None


@dataclass
class SchemaLaden:
    name: str
    id: Optional[int] = None


@dataclass
class SchemaSecurities:
    name: str
    isin: str
    ticker: str  # (stock, etf, crypto)
    instrument: str
    id:    Optional[int] = None


@dataclass
class SchemaAktienKurs:
    aktien_id: int
    kurs: Decimal
    datum: datetime
    id: Optional[int] = None


@dataclass
class SchemaKontobewegung:
    user_id: int
    name: str
    betrag: Decimal
    kategorie_id: int
    konto_id: int
    type_id: int
    datum: datetime
    id: Optional[int] = None


@dataclass
class SchemaKontostand:
    user_id: int
    konto_id: int
    kontostand: Decimal
    datum: datetime
    id: Optional[int] = None


@dataclass
class SchemaDepotbewegung:
    user_id: int
    konto_id: int
    aktien_id: int
    kategorie_id: int
    type_id: int
    betrag: Decimal
    anteile: Decimal
    datum: datetime
    id: Optional[int] = None


@dataclass
class SchemaDepotstand:
    user_id: int
    konto_id: int
    aktien_id: int
    summe_betrag: Decimal
    summe_anteil: Decimal
    wert: Decimal
    entwicklung: Decimal
    datum: datetime
    id: Optional[int] = None


@dataclass
class SchemaSparziel:
    user_id: int
    ausgangs_konto_id: int
    kategorie_id: int
    betrag: Decimal
    start_datum: datetime
    next_due: datetime
    sparrate_e: Decimal
    sparrate_p: Decimal
    verwendungszweck: str
    id: Optional[int] = None


@dataclass
class SchemaMonthlyCosts:
    user_id: int
    name: str
    kategorie_id: int
    start_datum: datetime
    next_due: datetime
    active: bool
    id: Optional[int] = None
    ausgangs_konto_id: Optional[int] = None
    eingangs_konto_id: Optional[int] = None
    aktien_id: Optional[int] = None
    anteil: Optional[Decimal] = None
    betrag: Optional[Decimal] = None


@dataclass
class SchemaReceipt:
    user_id: int
    name: str
    betrag: Decimal
    kategorie_id: int
    konto_id: int
    laden_id: int
    datum: datetime
    id: Optional[int] = None
