"""
Supabase Configuration Helper for SegurifAI x PAQ
This module provides utilities for connecting to Supabase.

Usage:
    1. Set environment variables (see .env.railway.example)
    2. Import this module where needed
    3. Use get_supabase_client() for Supabase operations
"""

import os
from functools import lru_cache

# Check if supabase-py is installed
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase-py not installed. Run: pip install supabase")


@lru_cache(maxsize=1)
def get_supabase_client() -> 'Client':
    """
    Get a cached Supabase client instance.

    Returns:
        Supabase Client instance

    Raises:
        ImportError: If supabase-py is not installed
        ValueError: If SUPABASE_URL or SUPABASE_ANON_KEY is not set
    """
    if not SUPABASE_AVAILABLE:
        raise ImportError("supabase-py is not installed. Run: pip install supabase")

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
        )

    return create_client(url, key)


def get_database_url() -> str:
    """
    Get the database URL for Django, prioritizing DATABASE_URL env var.
    Falls back to constructing URL from individual DB_ variables.

    Returns:
        PostgreSQL connection string
    """
    # First, try DATABASE_URL (Railway/Supabase standard)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    # Fallback: construct from individual variables
    db_name = os.environ.get("DB_NAME", "postgres")
    db_user = os.environ.get("DB_USER", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def parse_database_url(url: str) -> dict:
    """
    Parse a DATABASE_URL into Django DATABASES dict format.

    Args:
        url: PostgreSQL connection string

    Returns:
        Dict with Django database configuration
    """
    import re

    # Pattern for postgresql://user:password@host:port/dbname
    pattern = r"postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<name>\w+)"
    match = re.match(pattern, url)

    if not match:
        raise ValueError(f"Invalid DATABASE_URL format: {url}")

    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': match.group('name'),
        'USER': match.group('user'),
        'PASSWORD': match.group('password'),
        'HOST': match.group('host'),
        'PORT': match.group('port'),
        'OPTIONS': {
            'sslmode': 'require',  # Supabase requires SSL
        },
    }


# Django settings helper
def get_django_database_config() -> dict:
    """
    Get Django DATABASES configuration for Supabase/Railway.

    Returns:
        Dict suitable for Django DATABASES setting
    """
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return parse_database_url(database_url)

    # Fallback to individual variables
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': os.environ.get('DB_SSLMODE', 'prefer'),
        },
    }


# Test connection
if __name__ == "__main__":
    print("Testing Supabase configuration...")

    try:
        db_url = get_database_url()
        print(f"Database URL: {db_url[:50]}...")

        config = get_django_database_config()
        print(f"Django config: HOST={config['HOST']}, NAME={config['NAME']}")

        if SUPABASE_AVAILABLE:
            client = get_supabase_client()
            print("Supabase client created successfully!")
        else:
            print("Supabase client not available (supabase-py not installed)")

    except Exception as e:
        print(f"Error: {e}")
