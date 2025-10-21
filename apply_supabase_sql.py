import os
import sys

import psycopg2


def _resolve_db_url() -> str:
    # Priority: env var, then config/secrets
    db_url = os.environ.get("SUPABASE_DB_URL", "").strip()
    if db_url:
        return db_url
    try:
        # Lazy import to avoid hard dependency if not available
        import config  # type: ignore

        # config.get_secret will pull from env or streamlit secrets
        value = getattr(config, "get_secret")("SUPABASE_DB_URL", "").strip()
        if value:
            return value
    except Exception:
        pass
    return ""


def main():
    sql_file = os.environ.get("SQL_FILE", "database_rls_policies.sql")
    db_url = _resolve_db_url()

    if not db_url:
        print(
            "ERROR: Missing SUPABASE_DB_URL (Postgres connection string). Set it in env or streamlit secrets."
        )
        sys.exit(1)

    if not os.path.exists(sql_file):
        print(f"ERROR: SQL file not found: {sql_file}")
        sys.exit(1)

    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
        print("Applied SQL successfully.")
    except Exception as e:
        print(f"ERROR applying SQL: {e}")
        sys.exit(2)
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
