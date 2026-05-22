"""
src/db/queries.py
─────────────────
All SQL queries for the CRM pipeline — one function per query.
No raw SQL scattered across the codebase.

Part 1 (DB Modeling) & Part 2 (Lead Retrieval) live here.
"""

import psycopg2.extras
from typing import Optional
from src.db.connection import get_connection
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
SCHEMA = settings.postgres_schema


# ── Part 2: Lead Retrieval ─────────────────────────────────────────────────────

def get_leads_by_owner(owner_email: str) -> list[dict]:
    """
    Retrieve all leads assigned to a specific sales rep.

    Args:
        owner_email: e.g. "rep@company.com"

    Returns:
        List of lead dicts with keys: lead_id, lead_name, lead_email, status, created_at
    """
    sql = f"""
        SELECT
            lead_id,
            owner_email,
            lead_name,
            lead_email,
            status,
            created_at
        FROM {SCHEMA}.leads_raw
        WHERE owner_email = %s
        ORDER BY created_at DESC
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (owner_email,))
            results = cur.fetchall()
            logger.info(f"Found {len(results)} leads for owner: {owner_email}")
            return [dict(row) for row in results]


def get_activities_for_lead(lead_id: str) -> list[dict]:
    """
    Retrieve all CRM activities for a single lead, sorted chronologically.

    Args:
        lead_id: The lead's unique identifier

    Returns:
        List of activity dicts with raw_json parsed
    """
    sql = f"""
        SELECT
            activity_id,
            lead_id,
            activity_type,
            activity_timestamp,
            raw_json
        FROM {SCHEMA}.lead_activites_raw
        WHERE lead_id = %s
        ORDER BY activity_timestamp ASC
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (lead_id,))
            results = cur.fetchall()
            logger.info(f"Found {len(results)} activities for lead: {lead_id}")
            return [dict(row) for row in results]


def get_all_activities_for_owner(owner_email: str) -> dict[str, list[dict]]:
    """
    Convenience: returns leads + their activities grouped by lead_id.
    Used as the entry point for the LangGraph retrieve_activities node.

    Returns:
        { lead_id: [activity, activity, ...], ... }
    """
    leads = get_leads_by_owner(owner_email)
    timeline: dict[str, list[dict]] = {}

    for lead in leads:
        lead_id = lead["lead_id"]
        activities = get_activities_for_lead(lead_id)
        timeline[lead_id] = {
            "lead": lead,
            "activities": activities,
        }

    return timeline


def get_nurture_content(limit: int = 500) -> list[dict]:
    """
    Fetch all nurture content for embedding into Pinecone.
    Used once during the embedding pipeline setup.
    """
    sql = f"""
        SELECT *
        FROM {SCHEMA}.ai_nurturing_content
        LIMIT %s
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            results = cur.fetchall()
            logger.info(f"Fetched {len(results)} nurture content rows")
            return [dict(row) for row in results]


def get_crm_users() -> list[dict]:
    """
    Fetch sales rep list from CRM users table.
    Useful for driving the pipeline per rep.
    """
    sql = f"SELECT * FROM {SCHEMA}.close_crm_users_raw ORDER BY 1"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(row) for row in cur.fetchall()]
