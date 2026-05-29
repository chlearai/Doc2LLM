import os
from pathlib import Path

# Load .env file manually if it exists to support local development
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

from app.limiter import ConversionLimiter
from app.repository import InMemoryConversionRepository, SupabaseConversionRepository
from app.services import ConversionManager
from app.storage import InMemoryMarkdownStorage, SupabaseMarkdownStorage

# Read environment variables
supabase_url = os.getenv("SUPABASE_URL")
service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
storage_bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "markdown-outputs")

# Concurrency configurations
max_active = int(os.getenv("MAX_ACTIVE_CONVERSIONS", "3"))
max_pending = int(os.getenv("MAX_PENDING_CONVERSIONS", "10"))
timeout_seconds = int(os.getenv("CONVERSION_TIMEOUT_SECONDS", "300"))
temp_root_dir = os.getenv("TEMP_CONVERSION_DIR", "/tmp/conversions")

if supabase_url and service_role_key:
    repository = SupabaseConversionRepository(supabase_url, service_role_key)
    storage = SupabaseMarkdownStorage(supabase_url, service_role_key, storage_bucket)
else:
    repository = InMemoryConversionRepository()
    storage = InMemoryMarkdownStorage(storage_bucket)

_manager = ConversionManager(
    repository=repository,
    storage=storage,
    limiter=ConversionLimiter(max_active=max_active, max_pending=max_pending),
    temp_root=Path(temp_root_dir),
    timeout_seconds=timeout_seconds,
)


def get_conversion_manager() -> ConversionManager:
    return _manager
