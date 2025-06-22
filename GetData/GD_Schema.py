from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SchemaEinkauf:
    name: str
    betrag: Decimal
    kategorie: str
    konto: str
    ausgabentyp: str
    datum: datetime


@dataclass
class SchemaScheduler:
    name: str
    kategorie: str
    start_datum: datetime
    next_due: datetime
    active: bool
    konto_aus: Optional[str] = None
    konto_ein: Optional[str] = None
    wertpapier: Optional[str] = None
    anteile: Optional[Decimal] = None
    betrag: Optional[Decimal] = None


@dataclass
class SchemaWertpapierInfo:
    name: str
    isin: str
    ticker: str  # (stock, etf, crypto)
    instrument: str
