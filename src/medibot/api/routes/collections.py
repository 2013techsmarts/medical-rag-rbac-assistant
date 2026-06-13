from fastapi import APIRouter, Depends, HTTPException

from medibot.api.dependencies import get_current_role
from medibot.auth.roles import ROLE_ACCESS

router = APIRouter()


@router.get("/collections", tags=["collections"])
def get_my_collections(current_role: str = Depends(get_current_role)):
    """Get the collections accessible by the current authenticated user's role."""
    collections = ROLE_ACCESS.get(current_role, [])
    return {"role": current_role, "collections": collections}


@router.get("/collections/{role}", tags=["collections"])
def get_collections_by_role(role: str, current_role: str = Depends(get_current_role)):
    """Get the collections accessible by a specific role (requires authorization)."""
    # Security check: only allow users to check their own role, unless they are admin
    if current_role != "admin" and current_role != role:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You can only query collections for your own role.",
        )
    
    if role not in ROLE_ACCESS:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{role}' not found in role registry.",
        )

    collections = ROLE_ACCESS.get(role, [])
    return {"role": role, "collections": collections}
