from pathlib import Path

from app.limiter import ConversionLimiter
from app.repository import InMemoryConversionRepository
from app.services import ConversionManager
from app.storage import InMemoryMarkdownStorage


_manager = ConversionManager(
    repository=InMemoryConversionRepository(),
    storage=InMemoryMarkdownStorage(),
    limiter=ConversionLimiter(max_active=2, max_pending=10),
    temp_root=Path("/tmp/conversions"),
    timeout_seconds=300,
)


def get_conversion_manager() -> ConversionManager:
    return _manager
