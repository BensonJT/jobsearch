import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import List
from backend.models import JobListing

def get_connection():
    """Return a connection to the PostgreSQL database using DATABASE_URL."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def ensure_schema():
    """Create the job_listings table if it does not exist. Call once at startup."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS job_listings (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    is_remote BOOLEAN,
                    posted_at TIMESTAMPTZ,
                    description TEXT,
                    salary TEXT,
                    source TEXT,
                    match_score INTEGER,
                    search_keywords TEXT,
                    harvested_at TIMESTAMPTZ DEFAULT NOW(),
                    status TEXT DEFAULT 'new'
                );
            """)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def upsert_listings(listings: List[JobListing], search_keywords: str):
    """Upsert a list of JobListing objects. Preserve existing status values."""
    if not listings:
        return

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Prepare data for upsert
            values = []
            for job in listings:
                values.append((
                    job.url,
                    job.title,
                    job.company,
                    job.location,
                    job.is_remote,
                    job.posted_at,
                    job.description,
                    job.salary,
                    job.source,
                    job.match_score,
                    search_keywords
                ))

            # Upsert logic: on conflict (url), update all but status
            # Preserve human-set status by not including it in DO UPDATE SET
            query = """
                INSERT INTO job_listings (
                    url, title, company, location, is_remote, posted_at, 
                    description, salary, source, match_score, search_keywords
                ) VALUES %s
                ON CONFLICT (url) DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    is_remote = EXCLUDED.is_remote,
                    posted_at = EXCLUDED.posted_at,
                    description = EXCLUDED.description,
                    salary = EXCLUDED.salary,
                    source = EXCLUDED.source,
                    match_score = EXCLUDED.match_score,
                    search_keywords = EXCLUDED.search_keywords,
                    harvested_at = NOW();
            """
            # This DO UPDATE SET does NOT update 'status', so status is preserved.

            execute_values(cur, query, values)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_new_listings() -> List[dict]:
    """Return all rows with status='new', ordered by match_score DESC."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT match_score, title, company, location, posted_at, is_remote, url, source, status
                FROM job_listings
                WHERE status = 'new'
                ORDER BY match_score DESC;
            """)
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
            return results
    finally:
        conn.close()
