"""Supabase client configuration and utilities."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from supabase import create_client, Client

# Supabase configuration - from user provided credentials
SUPABASE_URL = "https://zndtfqdufpahwbmevkuw.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpuZHRmcWR1ZnBhaHdibWV2a3V3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzOTY5NjYsImV4cCI6MjA4NTk3Mjk2Nn0.9U6t5-2UEBC0git0FlsClz38ldM-4AOozD3HUZ-0a8M"


@lru_cache()
def get_supabase_client() -> Client:
    """Get or create Supabase client (singleton)."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_supabase_client_with_token(access_token: str) -> Client:
    """Get Supabase client authenticated with user token."""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.auth.set_session(access_token, refresh_token="")
    return client
