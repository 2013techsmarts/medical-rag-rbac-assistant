from qdrant_client import QdrantClient

from medibot.config.settings import settings


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port
    )