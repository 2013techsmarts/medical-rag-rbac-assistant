from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["system"])
def health_check():
    """Simple API status health check endpoint."""
    return {"status": "ok"}
