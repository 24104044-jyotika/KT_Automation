from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()

import os
from supabase import create_client, Client
 
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "https://gjnnrbbbqcpgarqpsjuk.supabase.co")
SUPABASE_KEY: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdqbm5yYmJicWNwZ2FycXBzanVrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTU3NjkwNCwiZXhwIjoyMDkxMTUyOTA0fQ.EIpvZL6drrvlkpt4FAJbT2LKcggNwW-thXXC2D9Ofik")  # Use service role key for backend
 
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")
 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)