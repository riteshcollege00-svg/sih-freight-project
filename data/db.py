"""
Database Connection and Execution Abstraction
SIH 2026: Freight Forecasting and Intelligent Vessel Chartering for Bulk Cargo
Member 1: Data & Domain Foundation

Supports:
- PostgreSQL 16+ via psycopg / psycopg2 (Primary)
- SQLite3 (Local offline testing / standalone demo verification)
"""

import os
import re
import sys
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Robust .env loader with no external dependency required
def load_dotenv_custom(dotenv_path: Optional[Path] = None) -> Dict[str, str]:
    if dotenv_path is None:
        dotenv_path = Path(__file__).resolve().parent.parent / ".env"
    env_vars = {}
    if dotenv_path.exists():
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    env_vars[k] = v
                    if k not in os.environ:
                        os.environ[k] = v
    return env_vars

load_dotenv_custom()

# Environment variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "freight_chartering")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/freight_chartering_demo.db")

# Detect available postgres driver
PSYCOPG_AVAILABLE = False
PSYCOPG_VERSION = None

try:
    import psycopg
    PSYCOPG_AVAILABLE = True
    PSYCOPG_VERSION = 3
except ImportError:
    try:
        import psycopg2
        PSYCOPG_AVAILABLE = True
        PSYCOPG_VERSION = 2
    except ImportError:
        PSYCOPG_AVAILABLE = False


class DatabaseConnection:
    """Unified Database connection manager for PostgreSQL with SQLite fallback."""

    def __init__(self, force_sqlite: bool = False):
        self.force_sqlite = force_sqlite
        self.db_type = "sqlite" if force_sqlite else "unknown"
        self._conn = None
        self._determine_driver()

    def _determine_driver(self):
        if self.force_sqlite:
            self.db_type = "sqlite"
            return

        if PSYCOPG_AVAILABLE:
            try:
                # Test postgres connection
                if PSYCOPG_VERSION == 3:
                    conn = psycopg.connect(
                        host=POSTGRES_HOST,
                        port=POSTGRES_PORT,
                        dbname=POSTGRES_DB,
                        user=POSTGRES_USER,
                        password=POSTGRES_PASSWORD,
                        connect_timeout=3
                    )
                    conn.close()
                    self.db_type = "postgres"
                    return
                elif PSYCOPG_VERSION == 2:
                    conn = psycopg2.connect(
                        host=POSTGRES_HOST,
                        port=POSTGRES_PORT,
                        dbname=POSTGRES_DB,
                        user=POSTGRES_USER,
                        password=POSTGRES_PASSWORD,
                        connect_timeout=3
                    )
                    conn.close()
                    self.db_type = "postgres"
                    return
            except Exception:
                # Postgres connection failed, fallback to SQLite for local execution
                self.db_type = "sqlite"
        else:
            self.db_type = "sqlite"

    def get_raw_connection(self):
        if self.db_type == "postgres":
            if PSYCOPG_VERSION == 3:
                return psycopg.connect(
                    host=POSTGRES_HOST,
                    port=POSTGRES_PORT,
                    dbname=POSTGRES_DB,
                    user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD
                )
            else:
                return psycopg2.connect(
                    host=POSTGRES_HOST,
                    port=POSTGRES_PORT,
                    dbname=POSTGRES_DB,
                    user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD
                )
        else:
            db_file = Path(__file__).resolve().parent.parent / SQLITE_DB_PATH
            db_file.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db_file))
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn

    def convert_pg_sql_to_sqlite(self, pg_sql: str) -> str:
        """Translates PostgreSQL DDL syntax to SQLite-compatible DDL for offline testing."""
        sql = pg_sql
        # Remove CREATE EXTENSION
        sql = re.sub(r'CREATE\s+EXTENSION\s+[^;]+;', '', sql, flags=re.IGNORECASE)
        # Replace BIGSERIAL / SERIAL with INTEGER PRIMARY KEY AUTOINCREMENT
        sql = re.sub(r'\bBIGSERIAL\s+PRIMARY\s+KEY\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bSERIAL\s+PRIMARY\s+KEY\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql, flags=re.IGNORECASE)
        # Replace TIMESTAMPTZ with TIMESTAMP
        sql = re.sub(r'\bTIMESTAMPTZ\b', 'TIMESTAMP', sql, flags=re.IGNORECASE)
        # Replace NUMERIC(x, y) with REAL
        sql = re.sub(r'\bNUMERIC\(\s*\d+\s*,\s*\d+\s*\)', 'REAL', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bNUMERIC\b', 'REAL', sql, flags=re.IGNORECASE)
        # Replace VARCHAR(x) with TEXT
        sql = re.sub(r'\bVARCHAR\(\s*\d+\s*\)', 'TEXT', sql, flags=re.IGNORECASE)
        # Remove CASCADE only from DROP TABLE statements
        sql = re.sub(r'(DROP\s+TABLE\s+[^;]+?)\s+CASCADE\s*;', r'\1;', sql, flags=re.IGNORECASE)
        return sql

    def init_schema(self, schema_file: Optional[Path] = None):
        if schema_file is None:
            schema_file = Path(__file__).resolve().parent / "schema" / "001_initial_schema.sql"

        with open(schema_file, "r", encoding="utf-8") as f:
            sql_content = f.read()

        conn = self.get_raw_connection()
        try:
            cur = conn.cursor()
            if self.db_type == "postgres":
                cur.execute(sql_content)
                conn.commit()
            else:
                sqlite_sql = self.convert_pg_sql_to_sqlite(sql_content)
                cur.executescript(sqlite_sql)
                conn.commit()
            cur.close()
        finally:
            conn.close()

    def execute_query(self, sql: str, params: Optional[Union[Tuple, Dict]] = None):
        conn = self.get_raw_connection()
        try:
            cur = conn.cursor()
            # Convert %s placeholders to ? if SQLite
            if self.db_type == "sqlite" and "%s" in sql:
                sql = sql.replace("%s", "?")
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            conn.commit()
            cur.close()
        finally:
            conn.close()

    def execute_many(self, sql: str, params_list: List[Tuple]):
        if not params_list:
            return
        conn = self.get_raw_connection()
        try:
            cur = conn.cursor()
            if self.db_type == "sqlite":
                if "%s" in sql:
                    sql = sql.replace("%s", "?")
                # Normalize any date/datetime objects to ISO string for sqlite3
                sanitized_params = []
                for row in params_list:
                    sanitized_row = tuple(
                        val.isoformat() if hasattr(val, "isoformat") else val
                        for val in row
                    )
                    sanitized_params.append(sanitized_row)
                params_list = sanitized_params
            cur.executemany(sql, params_list)
            conn.commit()
            cur.close()
        finally:
            conn.close()

    def fetch_all(self, sql: str, params: Optional[Tuple] = None) -> List[Tuple]:
        conn = self.get_raw_connection()
        try:
            cur = conn.cursor()
            if self.db_type == "sqlite" and "%s" in sql:
                sql = sql.replace("%s", "?")
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            results = cur.fetchall()
            cur.close()
            return results
        finally:
            conn.close()

    def fetch_one(self, sql: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        conn = self.get_raw_connection()
        try:
            cur = conn.cursor()
            if self.db_type == "sqlite" and "%s" in sql:
                sql = sql.replace("%s", "?")
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            result = cur.fetchone()
            cur.close()
            return result
        finally:
            conn.close()

    def get_table_row_count(self, table_name: str) -> int:
        res = self.fetch_one(f"SELECT COUNT(*) FROM {table_name}")
        return res[0] if res else 0


db = DatabaseConnection()
