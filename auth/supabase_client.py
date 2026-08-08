import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load variables from .env into the environment
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set in your .env file"
    )

# Single shared Supabase client, imported by other modules
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)