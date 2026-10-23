import sqlite3
from collections.abc import Iterator
from contextlib import closing

from app.config import settings
from app.security import hash_password


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer',
    points INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total REAL NOT NULL,
    status TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vouchers (
    code TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    cost_points INTEGER NOT NULL,
    value REAL NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);
"""


def get_db() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with closing(_connect()) as conn:
        _create_and_seed(conn)


def _create_and_seed(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        return

    conn.executemany(
        "INSERT INTO users (email, name, password_hash, role, points) VALUES (?, ?, ?, ?, ?)",
        [
            (settings.admin_email, "Admin", hash_password(settings.admin_password), "admin", 0),
            ("anna@example.com", "Anna Schmidt", hash_password("anna1234"), "customer", 500),
            ("ben@example.com", "Ben Weber", hash_password("ben12345"), "customer", 120),
        ],
    )
    conn.executemany(
        "INSERT INTO orders (user_id, total, status, shipping_address) VALUES (?, ?, ?, ?)",
        [
            (2, 23.95, "delivered", "Hauptstr. 1, 76131 Karlsruhe"),
            (2, 8.45, "shipped", "Hauptstr. 1, 76131 Karlsruhe"),
            (3, 41.10, "delivered", "Bahnhofstr. 7, 10115 Berlin"),
        ],
    )
    conn.executemany(
        "INSERT INTO vouchers (code, user_id, cost_points, value) VALUES (?, ?, ?, ?)",
        [
            ("ANNA-5EUR", 2, 300, 5.0),
            ("BEN-2EUR", 3, 100, 2.0),
        ],
    )
    conn.commit()
