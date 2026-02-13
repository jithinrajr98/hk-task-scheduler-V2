import os

from supabase import create_client, Client


TABLE = "staff_schedule"


def get_client() -> Client:
    """Create a Supabase client using env vars or Streamlit secrets."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_API_KEY")

    if not url or not key:
        try:
            import streamlit as st
            url = url or st.secrets["SUPABASE_URL"]
            key = key or st.secrets["SUPABASE_API_KEY"]
        except Exception:
            pass

    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_API_KEY")

    return create_client(url, key)


def push_schedule(schedule: list[dict]) -> None:
    """Replace all rows in staff_schedule with the new schedule."""
    client = get_client()
    # Delete existing rows
    client.table(TABLE).delete().neq("id", 0).execute()
    # Insert new rows (strip any extra keys, keep only the columns we need)
    columns = {"name", "day", "shift_name", "start_time", "end_time"}
    rows = [{k: v for k, v in row.items() if k in columns} for row in schedule]
    if rows:
        client.table(TABLE).insert(rows).execute()


def load_schedule() -> list[dict]:
    """Load all rows from staff_schedule table."""
    client = get_client()
    response = client.table(TABLE).select("name, day, shift_name, start_time, end_time").execute()
    return response.data
