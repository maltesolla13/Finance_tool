from decimal import Decimal
from pydantic.dataclasses import dataclass
from datetime import date
from typing import Optional, List


@dataclass
class SchemaOption:
    id: Optional[int] = None
    name: Optional[str] = None


@dataclass
class SchemaKonto:
    name: Optional[str] = None
    id: Optional[int] = None
    user_ids: Optional[List[int]] = None


@dataclass
class SchemaUser:
    name: Optional[str] = None
    id: Optional[int] = None


@dataclass
class SchemaKategorie:
    name: Optional[str] = None
    id: Optional[int] = None


@dataclass
class SchemaAusgabentyp:
    name: Optional[str] = None
    id: Optional[int] = None


@dataclass
class SchemaLaden:
    name: Optional[str] = None
    id: Optional[int] = None


@dataclass
class SchemaSecurities:
    name: Optional[str] = None
    isin: Optional[str] = None
    ticker: Optional[str] = None  # (stock, etf, crypto)
    instrument: Optional[str] = None
    id:    Optional[int] = None


@dataclass
class SchemaAktienKurs:
    securities_id: Optional[int] = None
    kurs: Optional[Decimal] = None
    datum: Optional[date] = None
    id: Optional[int] = None


@dataclass
class SchemaKontobewegung:
    user_id: Optional[int] = None
    name: Optional[str] = None
    betrag: Optional[Decimal] = None
    kategorie_id: Optional[int] = None
    konto_id: Optional[int] = None
    type: Optional[str] = None
    datum: Optional[date] = None
    id: Optional[int] = None


@dataclass
class SchemaKontostand:
    user_id: Optional[int] = None
    konto_id: Optional[int] = None
    kontostand: Optional[Decimal] = None
    datum: Optional[date] = None
    id: Optional[int] = None


@dataclass
class SchemaDepotbewegung:
    user_id: Optional[int] = None
    konto_id: Optional[int] = None
    ausgangs_konto_id: Optional[int] = None
    eingangs_konto_id: Optional[int] = None
    securities_id: Optional[int] = None
    kategorie_id: Optional[int] = None
    type: Optional[str] = None
    betrag: Optional[Decimal] = None
    anteile: Optional[Decimal] = None
    datum: Optional[date] = None
    id: Optional[int] = None


@dataclass
class SchemaDepotstand:
    user_id: Optional[int] = None
    konto_id: Optional[int] = None
    securities_id: Optional[int] = None
    summe_betrag: Optional[Decimal] = None
    summe_anteil: Optional[Decimal] = None
    wert: Optional[Decimal] = None
    entwicklung: Optional[Decimal] = None
    datum: Optional[date] = None
    id: Optional[int] = None


@dataclass
class SchemaSparziel:
    name: Optional[str] = None
    user_id: Optional[int] = None
    konto_id: Optional[int] = None
    kategorie_id: Optional[int] = None
    betrag: Optional[Decimal] = None
    start_datum: Optional[date] = None
    end_datum: Optional[date] = None
    sparrate_e: Optional[Decimal] = None
    sparrate_p: Optional[Decimal] = None
    id: Optional[int] = None


@dataclass
class SchemaSavingsExecution:
    id: Optional[int] = None
    savings_id: Optional[int] = None
    user_id: Optional[int] = None
    konto_id: Optional[int] = None
    kategorie_id: Optional[int] = None
    income_kontobewegung_id: Optional[int] = None
    execution_month: Optional[str] = None
    income_amount: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    status: Optional[str] = None


@dataclass
class SchemaMonthlyCosts:
    user_id: Optional[int] = None
    name: Optional[str] = None
    kategorie_id: Optional[int] = None
    start_datum: Optional[date] = None
    next_due: Optional[date] = None
    active: Optional[bool] = None
    id: Optional[int] = None
    ausgangs_konto_id: Optional[int] = None
    eingangs_konto_id: Optional[int] = None
    securities_id: Optional[int] = None
    anteil: Optional[Decimal] = None
    betrag: Optional[Decimal] = None
    repeat_type: Optional[str] = None
    custom_interval: Optional[int] = None
    custom_unit: Optional[str] = None


@dataclass
class SchemaMonthlyCostsExecution:
    id: Optional[int] = None
    monthlycost_id: Optional[int] = None
    user_id: Optional[int] = None
    name: Optional[str] = None
    betrag: Optional[Decimal] = None
    anteil: Optional[Decimal] = None
    securities_id: Optional[int] = None
    kategorie_id: Optional[int] = None
    ausgangs_konto_id: Optional[int] = None
    eingangs_konto_id: Optional[int] = None
    execution_datum: Optional[date] = None
    status: Optional[str] = None


@dataclass
class SchemaReceipt:
    user_id: Optional[int] = None
    name: Optional[str] = None
    betrag: Optional[Decimal] = None
    kategorie_id: Optional[int] = None
    konto_id: Optional[int] = None
    laden_id: Optional[int] = None
    datum: Optional[date] = None
    id: Optional[int] = None
