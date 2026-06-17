import json
import re
import sys
import sqlite3
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path

import requests


OZ_PER_KG = Decimal("32.1507")


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


DB_FILE = app_dir() / "system_metali.db"
API_FILE = app_dir() / "KluczApi.json"

NBP_USD_PLN_URL = "https://api.nbp.pl/api/exchangerates/rates/a/usd/?format=json"

TRADINGVIEW_URLS = {
    "srebro": "https://www.tradingview.com/symbols/XAGUSD/?exchange=OANDA",
    "zloto": "https://www.tradingview.com/symbols/XAUUSD/?exchange=OANDA",
}

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

portfolio = []


# =========================
# API KEY
# =========================
def load_api_key() -> str:
    if not API_FILE.exists():
        return ""

    try:
        with open(API_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return str(data.get("gold_api_key", "")).strip()
    except Exception:
        return ""


GOLD_API_KEY = load_api_key()


def has_api_key() -> bool:
    return bool(GOLD_API_KEY)


def get_api_status_message() -> str:
    if has_api_key():
        return "Klucz API został poprawnie odczytany."
    return (
        "Brak klucza API. Utwórz plik KluczApi.json w folderze aplikacji "
        "i wpisz w nim własny klucz GoldAPI."
    )


# =========================
# SQLITE
# =========================
def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                metal TEXT NOT NULL,
                kg TEXT NOT NULL,
                oz TEXT NOT NULL,
                price_pln_oz TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS market_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_czas TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                metal TEXT NOT NULL,
                price_usd_oz TEXT,
                usd_pln TEXT,
                price_pln_oz TEXT
            )
        """)

        conn.commit()


# =========================
# FORMATOWANIE
# =========================
def q2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def q4(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def fmt2(value: Decimal) -> str:
    return format(q2(value), "f")


def fmt4(value: Decimal) -> str:
    return format(q4(value), "f")


# =========================
# KONWERSJE
# =========================
def convert_amount_to_kg_oz(amount: Decimal, unit: str) -> tuple[Decimal, Decimal]:
    if unit == "kg":
        return amount, amount * OZ_PER_KG
    return amount / OZ_PER_KG, amount


def convert_price_to_oz(price: Decimal, unit: str) -> Decimal:
    if unit == "kg":
        return price / OZ_PER_KG
    return price


# =========================
# API / DANE RYNKOWE
# =========================
def fetch_goldapi_price_usd_oz(metal: str) -> Decimal | None:
    if not has_api_key():
        return None

    code = "XAU" if metal == "zloto" else "XAG"
    url = f"https://app.goldapi.net/api/price/{code}/USD"

    headers = {
        "x-api-key": GOLD_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        price = Decimal(str(data.get("price", "0")))

        if price <= 0:
            return None

        return price

    except Exception:
        return None


def fetch_tradingview_price_usd_oz(metal: str) -> Decimal | None:
    if not has_api_key():
        return None

    url = TRADINGVIEW_URLS.get(metal)
    if not url:
        return None

    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text

        patterns = [
            r'"last_price"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
            r'"lp"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
            r'"price"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
            r'(?:XAGUSD|XAUUSD)[^0-9]{0,250}([0-9]{2,6}\.[0-9]+)',
        ]

        candidates = []

        for pattern in patterns:
            for match in re.findall(pattern, html):
                try:
                    value = Decimal(str(match))

                    if metal == "srebro" and Decimal("10") <= value <= Decimal("100"):
                        candidates.append(value)

                    if metal == "zloto" and Decimal("1000") <= value <= Decimal("10000"):
                        candidates.append(value)

                except InvalidOperation:
                    pass

        if not candidates:
            return None

        candidates.sort()
        return candidates[len(candidates) // 2]

    except Exception:
        return None


def fetch_metal_price_usd_oz(metal: str) -> Decimal | None:
    if not has_api_key():
        return None

    price = fetch_goldapi_price_usd_oz(metal)

    if price is not None:
        return price

    return fetch_tradingview_price_usd_oz(metal)


def fetch_usd_pln() -> Decimal | None:
    if not has_api_key():
        return None

    try:
        response = requests.get(NBP_USD_PLN_URL, timeout=10)
        response.raise_for_status()
        return Decimal(str(response.json()["rates"][0]["mid"]))
    except Exception:
        return None


def save_market_history(snapshot: dict) -> None:
    usd_pln = snapshot.get("usd_pln")

    if usd_pln is None:
        return

    with get_connection() as conn:
        for metal, key in [("srebro", "silver_usd_oz"), ("zloto", "gold_usd_oz")]:
            price_usd = snapshot.get(key)

            if price_usd is None:
                continue

            price_pln = price_usd * usd_pln

            conn.execute("""
                INSERT INTO market_history (
                    metal, price_usd_oz, usd_pln, price_pln_oz
                )
                VALUES (?, ?, ?, ?)
            """, (
                metal,
                str(price_usd),
                str(usd_pln),
                str(price_pln),
            ))

        conn.commit()


# =========================
# PORTFEL SQLITE
# =========================
def save_portfolio() -> None:
    """
    Funkcja zostaje dla zgodności z GUI.
    Przy SQLite zapis odbywa się bezpośrednio w add/delete.
    """
    pass


def load_portfolio() -> None:
    global portfolio

    init_db()

    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT data, metal, kg, oz, price_pln_oz
            FROM transactions
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()

    portfolio = []

    for row in rows:
        portfolio.append({
            "data": row[0],
            "metal": row[1],
            "kg": Decimal(str(row[2])),
            "oz": Decimal(str(row[3])),
            "price_pln_oz": Decimal(str(row[4])),
        })


# =========================
# LOGIKA
# =========================
def add_transaction(
    data: str,
    metal: str,
    amount: Decimal,
    unit: str,
    price: Decimal,
    price_unit: str,
    currency: str,
) -> None:
    init_db()

    if metal not in ("zloto", "srebro"):
        raise ValueError("Niepoprawny metal.")

    if unit not in ("kg", "oz"):
        raise ValueError("Niepoprawna jednostka ilości.")

    if price_unit not in ("kg", "oz"):
        raise ValueError("Niepoprawna jednostka ceny.")

    if currency not in ("pln", "usd"):
        raise ValueError("Niepoprawna waluta.")

    if amount <= 0:
        raise ValueError("Ilość musi być większa od 0.")

    if price <= 0:
        raise ValueError("Cena musi być większa od 0.")

    kg, oz = convert_amount_to_kg_oz(amount, unit)
    price_oz = convert_price_to_oz(price, price_unit)

    if currency == "usd":
        usd_pln = fetch_usd_pln()
        if usd_pln is None:
            raise ValueError(
                "Nie udało się pobrać kursu USD/PLN. "
                "Sprawdź plik KluczApi.json oraz połączenie z Internetem."
            )
        price_pln_oz = price_oz * usd_pln
    else:
        price_pln_oz = price_oz

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO transactions (
                data, metal, kg, oz, price_pln_oz
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            data,
            metal,
            str(kg),
            str(oz),
            str(price_pln_oz),
        ))

        conn.commit()

    load_portfolio()


def delete_transaction(index: int) -> None:
    init_db()

    if index < 0:
        raise IndexError("Niepoprawny indeks transakcji.")

    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT id
            FROM transactions
            ORDER BY id ASC
        """)

        ids = [row[0] for row in cursor.fetchall()]

        if index >= len(ids):
            raise IndexError("Niepoprawny indeks transakcji.")

        transaction_id = ids[index]

        conn.execute("""
            DELETE FROM transactions
            WHERE id = ?
        """, (transaction_id,))

        conn.commit()

    load_portfolio()


def get_market_snapshot() -> dict:
    if not has_api_key():
        return {
            "api_key_ok": False,
            "api_message": get_api_status_message(),
            "usd_pln": None,
            "silver_usd_oz": None,
            "gold_usd_oz": None,
        }

    usd_pln = fetch_usd_pln()
    silver_usd = fetch_metal_price_usd_oz("srebro")
    gold_usd = fetch_metal_price_usd_oz("zloto")

    snapshot = {
        "api_key_ok": True,
        "api_message": get_api_status_message(),
        "usd_pln": usd_pln,
        "silver_usd_oz": silver_usd,
        "gold_usd_oz": gold_usd,
    }

    save_market_history(snapshot)

    return snapshot


def get_current_price_pln_oz(metal: str, snapshot: dict | None = None) -> Decimal | None:
    if snapshot is None:
        snapshot = get_market_snapshot()

    usd_pln = snapshot.get("usd_pln")
    if usd_pln is None:
        return None

    metal_usd = snapshot.get("gold_usd_oz") if metal == "zloto" else snapshot.get("silver_usd_oz")
    if metal_usd is None:
        return None

    return metal_usd * usd_pln


def calculate_transaction_details(tx: dict, snapshot: dict | None = None) -> dict:
    current_price_pln_oz = get_current_price_pln_oz(tx["metal"], snapshot)
    purchase_value = tx["oz"] * tx["price_pln_oz"]

    if current_price_pln_oz is None:
        current_value = Decimal("0")
        profit = Decimal("0")
        roi = Decimal("0")
    else:
        current_value = tx["oz"] * current_price_pln_oz
        profit = current_value - purchase_value
        roi = (profit / purchase_value * Decimal("100")) if purchase_value > 0 else Decimal("0")

    return {
        "purchase_price_pln_oz": tx["price_pln_oz"],
        "current_price_pln_oz": current_price_pln_oz,
        "purchase_value_pln": purchase_value,
        "current_value_pln": current_value,
        "profit_pln": profit,
        "roi_percent": roi,
    }


def calculate_summary(snapshot: dict | None = None) -> tuple[Decimal, Decimal, Decimal]:
    if snapshot is None:
        snapshot = get_market_snapshot()

    total_purchase = Decimal("0")
    total_current = Decimal("0")

    for tx in portfolio:
        details = calculate_transaction_details(tx, snapshot)
        total_purchase += details["purchase_value_pln"]
        total_current += details["current_value_pln"]

    profit = total_current - total_purchase
    return total_purchase, total_current, profit


def get_portfolio_rows(snapshot: dict | None = None) -> list[list[str]]:
    if snapshot is None:
        snapshot = get_market_snapshot()

    rows = []

    for i, tx in enumerate(portfolio, start=1):
        details = calculate_transaction_details(tx, snapshot)

        current_price = (
            fmt2(details["current_price_pln_oz"])
            if details["current_price_pln_oz"] is not None
            else "brak"
        )

        rows.append([
            str(i),
            tx["data"],
            tx["metal"],
            fmt4(tx["kg"]),
            fmt4(tx["oz"]),
            fmt2(details["purchase_price_pln_oz"]),
            current_price,
            fmt2(details["purchase_value_pln"]),
            fmt2(details["current_value_pln"]),
            fmt2(details["profit_pln"]),
            fmt2(details["roi_percent"]),
        ])

    return rows

def get_market_history(metal: str, limit: int = 100) -> list[tuple[str, str]]:
    init_db()

    if metal not in ("zloto", "srebro"):
        return []

    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT data_czas, price_pln_oz
            FROM market_history
            WHERE metal = ?
              AND price_pln_oz IS NOT NULL
            ORDER BY id DESC
            LIMIT ?
        """, (metal, limit))

        rows = cursor.fetchall()

    rows.reverse()
    return rows


init_db()