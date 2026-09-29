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