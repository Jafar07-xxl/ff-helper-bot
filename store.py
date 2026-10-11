"""SQLite storage for FF Helper language preferences and shop orders."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator


DB_PATH = Path(__file__).with_name("ff_helper.sqlite3")
AUTO_CANCEL_AFTER = timedelta(minutes=20)
ACTIVE_ORDER_STATUSES = (
    "awaiting_uid",
    "awaiting_payment_method",
    "awaiting_receipt",
)


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_store() -> None:
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL CHECK (language IN ('ru', 'tg'))
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_navigation (
                chat_id INTEGER PRIMARY KEY,
                menu_context TEXT NOT NULL CHECK (
                    menu_context IN ('language', 'main', 'shop')
                ),
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                language TEXT NOT NULL CHECK (language IN ('ru', 'tg')),
                package_id TEXT NOT NULL,
                diamonds INTEGER NOT NULL,
                price_tjs TEXT NOT NULL,
                free_fire_uid TEXT,
                payment_method TEXT,
                status TEXT NOT NULL CHECK (
                    status IN (
                        'awaiting_uid',
                        'awaiting_payment_method',
                        'awaiting_receipt',
                        'forwarding_receipt',
                        'pending_review',
                        'paid',
                        'rejected',
                        'cancelled'
                    )
                ),
                receipt_chat_id INTEGER,
                receipt_message_id INTEGER,
                admin_message_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS orders_user_status_idx ON orders (user_id, status)"
        )
        # If the bot stopped while copying a receipt, let the buyer send it again.
        # Any old review buttons remain harmless because their orders are not pending_review.
        connection.execute(
            """
            UPDATE orders
            SET status = 'awaiting_receipt', admin_message_id = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE status = 'forwarding_receipt'
            """
        )


def get_user_language(user_id: int) -> str | None:
    with _connection() as connection:
        row = connection.execute(
            "SELECT language FROM user_preferences WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return row["language"] if row else None


def save_user_language(user_id: int, language: str) -> None:
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO user_preferences (user_id, language)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
            """,
            (user_id, language),
        )


def save_chat_menu_context(chat_id: int, menu_context: str) -> None:
    if menu_context not in {"language", "main", "shop"}:
        raise ValueError("Invalid chat menu context")
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO chat_navigation (chat_id, menu_context)
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                menu_context = excluded.menu_context,
                updated_at = CURRENT_TIMESTAMP
            """,
            (chat_id, menu_context),
        )


def get_chat_menu_context(chat_id: int) -> str | None:
    with _connection() as connection:
        row = connection.execute(
            "SELECT menu_context FROM chat_navigation WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
    return row["menu_context"] if row else None


def create_order(
    user_id: int,
    chat_id: int,
    language: str,
    package_id: str,
    diamonds: int,
    price_tjs: str,
) -> dict:
    with _connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO orders (
                user_id, chat_id, language, package_id, diamonds, price_tjs, status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'awaiting_uid')
            """,
            (user_id, chat_id, language, package_id, diamonds, price_tjs),
        )
        row = connection.execute(
            "SELECT * FROM orders WHERE order_id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def get_active_order(user_id: int) -> dict | None:
    placeholders = ", ".join("?" for _ in ACTIVE_ORDER_STATUSES)
    with _connection() as connection:
        row = connection.execute(
            f"""
            SELECT * FROM orders
            WHERE user_id = ? AND status IN ({placeholders})
            ORDER BY order_id DESC LIMIT 1
            """,
            (user_id, *ACTIVE_ORDER_STATUSES),
        ).fetchone()
    return dict(row) if row else None


def cancel_expired_orders(now: datetime | None = None) -> list[dict]:
    """Cancel unpaid draft orders after 20 minutes and return their details."""
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    cutoff = (current_time.astimezone(timezone.utc) - AUTO_CANCEL_AFTER).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    placeholders = ", ".join("?" for _ in ACTIVE_ORDER_STATUSES)

    with _connection() as connection:
        rows = connection.execute(
            f"""
            SELECT * FROM orders
            WHERE status IN ({placeholders}) AND created_at <= ?
            ORDER BY order_id
            """,
            (*ACTIVE_ORDER_STATUSES, cutoff),
        ).fetchall()
        if not rows:
            return []

        order_ids = [row["order_id"] for row in rows]
        order_placeholders = ", ".join("?" for _ in order_ids)
        connection.execute(
            f"""
            UPDATE orders
            SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE order_id IN ({order_placeholders})
              AND status IN ({placeholders})
            """,
            (*order_ids, *ACTIVE_ORDER_STATUSES),
        )
    return [dict(row) for row in rows]


def cancel_draft_order(order_id: int, user_id: int) -> None:
    with _connection() as connection:
        connection.execute(
            """
            UPDATE orders
            SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND user_id = ?
              AND (
                  status IN ('awaiting_uid', 'awaiting_payment_method')
                  OR (status = 'awaiting_receipt' AND payment_method IS NULL)
              )
            """,
            (order_id, user_id),
        )


def save_free_fire_uid(order_id: int, user_id: int, free_fire_uid: str) -> bool:
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE orders
            SET free_fire_uid = ?, status = 'awaiting_payment_method',
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND user_id = ? AND status = 'awaiting_uid'
            """,
            (free_fire_uid, order_id, user_id),
        )
    return cursor.rowcount == 1


def confirm_free_fire_uid(order_id: int, user_id: int) -> bool:
    """Finish UID confirmation; awaiting_receipt with no method means choose payment."""
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE orders
            SET status = 'awaiting_receipt', updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND user_id = ?
              AND status = 'awaiting_payment_method'
              AND free_fire_uid IS NOT NULL
            """,
            (order_id, user_id),
        )
    return cursor.rowcount == 1


def reset_free_fire_uid(order_id: int, user_id: int) -> bool:
    """Clear an unconfirmed UID and ask the customer to enter it again."""
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE orders
            SET free_fire_uid = NULL, status = 'awaiting_uid',
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND user_id = ?
              AND status = 'awaiting_payment_method'
            """,
            (order_id, user_id),
        )
    return cursor.rowcount == 1


def save_payment_method(
    order_id: int,
    user_id: int,
    payment_method: str,
) -> bool:
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE orders
            SET payment_method = ?, updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND user_id = ?
              AND status = 'awaiting_receipt' AND payment_method IS NULL
            """,
            (payment_method, order_id, user_id),
        )
    return cursor.rowcount == 1


def begin_receipt_delivery(
    order_id: int,
    user_id: int,
    receipt_chat_id: int,
    receipt_message_id: int,
) -> bool:
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE orders
            SET status = 'forwarding_receipt',
                receipt_chat_id = ?, receipt_message_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND user_id = ?
              AND status = 'awaiting_receipt' AND payment_method IS NOT NULL
            """,
            (receipt_chat_id, receipt_message_id, order_id, user_id),
        )
    return cursor.rowcount == 1


def mark_receipt_pending_review(order_id: int, admin_message_id: int) -> bool:
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE orders
            SET status = 'pending_review', admin_message_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND status = 'forwarding_receipt'
            """,
            (admin_message_id, order_id),
        )
    return cursor.rowcount == 1


def restore_receipt_waiting(order_id: int) -> None:
    with _connection() as connection:
        connection.execute(
            """
            UPDATE orders
            SET status = 'awaiting_receipt', admin_message_id = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND status = 'forwarding_receipt'
            """,
            (order_id,),
        )


def get_order(order_id: int) -> dict | None:
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
    return dict(row) if row else None


def moderate_order(
    order_id: int,
    admin_message_id: int,
    new_status: str,
) -> tuple[dict | None, str]:
    if new_status not in {"paid", "rejected"}:
        raise ValueError("Invalid order decision")

    with _connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if not row:
            return None, "not_found"
        if row["status"] != "pending_review":
            return dict(row), "not_pending"
        if row["admin_message_id"] != admin_message_id:
            return dict(row), "wrong_message"

        cursor = connection.execute(
            """
            UPDATE orders
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND status = 'pending_review'
              AND admin_message_id = ?
            """,
            (new_status, order_id, admin_message_id),
        )
        updated = connection.execute(
            "SELECT * FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
    return (dict(updated), "updated") if cursor.rowcount == 1 else (dict(updated), "not_pending")
