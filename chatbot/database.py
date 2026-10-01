import os
from typing import List

from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

load_dotenv()

DB_URI = os.getenv("DB_URI") or ""
pool = ConnectionPool(
    conninfo=DB_URI,
    kwargs={"autocommit": True},
    min_size=1,
    max_size=5,
    open=False,
)


def init_db():
    """Initializes long-term storage table schemas."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS long_term_profiles (
                    user_id VARCHAR(255),
                    fact TEXT,
                    category VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_history_user_thread_created
                ON chat_history (user_id, thread_id, created_at, id);
            """)
            conn.commit()


def get_long_term_memories(user_id: str) -> str:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT fact, category FROM long_term_profiles WHERE user_id = %s;", (user_id,))
            rows = cur.fetchall()
    if not rows:
        return "No historical memory found for this user."
    return "\n".join(f"- {row[0]} (Category: {row[1]})" for row in rows)


def save_new_memories(user_id: str, facts: List) -> int:
    inserted_count = 0
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for fact in facts:
                cur.execute(
                    """
                    SELECT 1
                    FROM long_term_profiles
                    WHERE user_id = %s AND category = %s AND fact = %s
                    LIMIT 1;
                    """,
                    (user_id, fact.category, fact.fact),
                )
                if cur.fetchone() is not None:
                    continue

                cur.execute(
                    "INSERT INTO long_term_profiles (user_id, fact, category) VALUES (%s, %s, %s);",
                    (user_id, fact.fact, fact.category)
                )
                inserted_count += 1
            conn.commit()
    return inserted_count

def log_message_to_db(thread_id: str, user_id: str, role: str, content: str):
    """Inserts a clean text record of a conversation turn into the database."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_history (thread_id, user_id, role, content) 
                VALUES (%s, %s, %s, %s);
            """, (thread_id, user_id, role, content))
            conn.commit()


def list_chat_conversations(user_id: str) -> list[dict[str, str]]:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT history.thread_id,
                       (
                           SELECT content
                           FROM chat_history AS first_message
                           WHERE first_message.thread_id = history.thread_id
                             AND first_message.user_id = history.user_id
                             AND first_message.role = 'user'
                           ORDER BY first_message.created_at, first_message.id
                           LIMIT 1
                       ) AS title,
                       MAX(history.created_at) AS updated_at
                FROM chat_history AS history
                WHERE history.user_id = %s
                GROUP BY history.user_id, history.thread_id
                ORDER BY MAX(history.created_at) DESC;
            """, (user_id,))
            rows = cur.fetchall()

    return [
        {
            "session_id": row[0],
            "title": (row[1] or "New conversation")[:72],
            "updated_at": row[2].isoformat(),
        }
        for row in rows
    ]


def get_chat_history(user_id: str, thread_id: str) -> list[dict[str, str]]:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT role, content
                FROM chat_history
                WHERE user_id = %s AND thread_id = %s
                ORDER BY created_at, id;
            """, (user_id, thread_id))
            rows = cur.fetchall()

    return [{"role": row[0], "content": row[1]} for row in rows]