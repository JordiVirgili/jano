from fastapi import APIRouter, Depends

from argos.api.auth import verify_credentials

router = APIRouter(
    prefix="/api/v1/system",
    tags=["system"]
)

# Root path to verify the API is running
@router.get("/healthcheck")
def healthcheck(username: str = Depends(verify_credentials)):
    """Verify that the API is running."""
    return {"status": "API running", "version": "1.0.0", "authenticated_as": username}