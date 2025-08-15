# =============================
# Database Access Layer
# =============================
# All database operations for the Covenant Schedule Generator system.
# It handles schema creation, CRUD, and data integrity with clear business logic.

import sqlite3
from typing import List, Dict, Any

# --- Database Schema ---
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    name TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS covenants (
    covenant_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    description TEXT NOT NULL,
    frequency TEXT NOT NULL,
    owner_email TEXT NOT NULL,
    FOREIGN KEY(transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS schedules (
    schedule_id TEXT PRIMARY KEY,
    covenant_id TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(covenant_id) REFERENCES covenants(covenant_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_transaction_id ON transactions(transaction_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_covenants_covenant_id ON covenants(covenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_schedules_schedule_id ON schedules(schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedules_covenant_id ON schedules(covenant_id);
CREATE INDEX IF NOT EXISTS idx_schedules_due_date ON schedules(due_date);
"""


class Database:
    """
    Database access layer for the Covenant Schedule Generator.
    Handles schema creation, CRUD operations, and ensures data integrity.
    Uses SQLite for local storage with foreign key constraints and unique indices.
    """

    def __init__(self, db_path: str = 'schedules.db'):
        """
        Initialize the database connection and path.
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        """
        Context manager entry: opens the database connection, enforces foreign keys, and ensures schema is present.
        """
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys = ON;')
        self.conn.executescript(DB_SCHEMA)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit: commits and closes the database connection.
        """
        if self.conn:
            try:
                self.conn.commit()
            except Exception as e:
                print(f"[DB ERROR] Commit failed: {e}")
            self.conn.close()

    # =============================
    # Transaction Methods
    # =============================

    def save_transaction(self, transaction: Dict[str, Any]):
        """
        Insert a new transaction record. Enforces uniqueness of transaction_id.
        Args:
            transaction (dict): Dict with transaction_id, name, start_date, end_date
        Raises:
            ValueError: If transaction_id already exists.
        """
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT 1 FROM transactions WHERE transaction_id = ?", (transaction['transaction_id'],))
            if cur.fetchone():
                raise ValueError(f"Duplicate transaction_id found: {transaction['transaction_id']}")
            with self.conn:
                self.conn.execute(
                    """
                    INSERT INTO transactions (transaction_id, name, start_date, end_date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (transaction['transaction_id'], transaction.get('name', ''), transaction['start_date'], transaction['end_date'])
                )
        except Exception as e:
            print(f"[DB ERROR] save_transaction: {e}")
            raise

    # =============================
    # Covenant Methods
    # =============================

    def save_covenants(self, covenants: List[Dict[str, Any]]):
        """
        Bulk insert new covenant records. Enforces referential integrity and uniqueness.
        Args:
            covenants (list): List of covenant dicts
        Raises:
            ValueError: If referential integrity or uniqueness is violated.
        """
        try:
            for c in covenants:
                cur = self.conn.cursor()
                cur.execute("SELECT 1 FROM transactions WHERE transaction_id = ?", (c['transaction_id'],))
                if not cur.fetchone():
                    raise ValueError(f"Covenant {c['covenant_id']} references non-existent transaction_id {c['transaction_id']}")
                cur.execute("SELECT 1 FROM covenants WHERE covenant_id = ?", (c['covenant_id'],))
                if cur.fetchone():
                    raise ValueError(f"Duplicate covenant_id found: {c['covenant_id']}")
            with self.conn:
                self.conn.executemany(
                    """
                    INSERT INTO covenants (covenant_id, transaction_id, description, frequency, owner_email)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [(
                        c['covenant_id'], c['transaction_id'], c['description'], c['frequency'], c['owner_email']
                    ) for c in covenants]
                )
        except Exception as e:
            print(f"[DB ERROR] save_covenants: {e}")
            raise

    # =============================
    # Schedule Methods
    # =============================

    def save_schedules(self, schedules: List[Dict[str, Any]], holidays: List[str] = None):
        """
        Bulk insert new schedule records. Enforces uniqueness, referential integrity, and business rules.
        Args:
            schedules (list): List of schedule dicts
            holidays (list, optional): List of holiday dates as 'YYYY-MM-DD' strings
        Raises:
            ValueError: If any business rule is violated.
        """
        try:
            allowed_status = {'pending', 'completed', 'overdue', 'cancelled'}
            holiday_set = set(holidays) if holidays else set()
            batch_ids = set()
            for s in schedules:
                # Check for duplicate schedule_id in batch
                if s['schedule_id'] in batch_ids:
                    raise ValueError(f"Duplicate schedule_id in batch: {s['schedule_id']}")
                batch_ids.add(s['schedule_id'])
                # Check for uniqueness in DB
                cur = self.conn.cursor()
                cur.execute("SELECT 1 FROM schedules WHERE schedule_id = ?", (s['schedule_id'],))
                if cur.fetchone():
                    raise ValueError(f"Duplicate schedule_id found: {s['schedule_id']}")
                # Check foreign key
                cur.execute("SELECT 1 FROM covenants WHERE covenant_id = ?", (s['covenant_id'],))
                if not cur.fetchone():
                    raise ValueError(f"Schedule {s['schedule_id']} references non-existent covenant_id {s['covenant_id']}")
                # Check status field
                if s['status'] not in allowed_status:
                    raise ValueError(f"Schedule {s['schedule_id']} has invalid status: {s['status']}")
                # Check for holiday/weekend
                due_date = s['due_date']
                if due_date in holiday_set:
                    raise ValueError(f"Schedule {s['schedule_id']} due_date {due_date} falls on a holiday")
                from datetime import datetime
                dt = datetime.strptime(due_date, '%Y-%m-%d')
                if dt.weekday() >= 5:
                    raise ValueError(f"Schedule {s['schedule_id']} due_date {due_date} falls on a weekend")
            with self.conn:
                self.conn.executemany(
                    """
                    INSERT INTO schedules (schedule_id, covenant_id, due_date, status, period_start, period_end)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [(
                        s['schedule_id'], s['covenant_id'], s['due_date'], s['status'], s['period_start'], s['period_end']
                    ) for s in schedules]
                )
        except Exception as e:
            print(f"[DB ERROR] save_schedules: {e}")
            raise

    # =============================
    # Query Methods
    # =============================

    def get_schedules(self, covenant_id: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve schedules, optionally filtered by covenant_id.
        Args:
            covenant_id (str, optional): Filter schedules by this covenant_id
        Returns:
            list: List of schedule dicts
        """
        try:
            cur = self.conn.cursor()
            if covenant_id:
                cur.execute("SELECT * FROM schedules WHERE covenant_id = ?", (covenant_id,))
            else:
                cur.execute("SELECT * FROM schedules")
            return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"[DB ERROR] get_schedules: {e}")
            return []

    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Retrieve a transaction by transaction_id.
        Args:
            transaction_id (str): The transaction_id to retrieve
        Returns:
            dict or None: Transaction dict or None if not found
        """
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        except Exception as e:
            print(f"[DB ERROR] get_transaction: {e}")
            return None

    def get_covenants(self, transaction_id: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve covenants, optionally filtered by transaction_id.
        Args:
            transaction_id (str, optional): Filter covenants by this transaction_id
        Returns:
            list: List of covenant dicts
        """
        try:
            cur = self.conn.cursor()
            if transaction_id:
                cur.execute("SELECT * FROM covenants WHERE transaction_id = ?", (transaction_id,))
            else:
                cur.execute("SELECT * FROM covenants")
            return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"[DB ERROR] get_covenants: {e}")
            return []

    # =============================
    # Update/Delete Methods
    # =============================

    def update_schedule_status(self, schedule_id: str, status: str):
        """
        Update the status of a schedule entry.
        Args:
            schedule_id (str): The schedule_id to update
            status (str): New status value
        """
        try:
            with self.conn:
                self.conn.execute(
                    """
                    UPDATE schedules SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE schedule_id = ?
                    """,
                    (status, schedule_id)
                )
        except Exception as e:
            print(f"[DB ERROR] update_schedule_status: {e}")

    def delete_schedule(self, schedule_id: str):
        """
        Delete a schedule entry by schedule_id.
        Args:
            schedule_id (str): The schedule_id to delete
        """
        try:
            with self.conn:
                self.conn.execute(
                    "DELETE FROM schedules WHERE schedule_id = ?", (schedule_id,)
                )
        except Exception as e:
            print(f"[DB ERROR] delete_schedule: {e}")
