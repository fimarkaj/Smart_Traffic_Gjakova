from fastapi import APIRouter, Depends
from auth import get_current_user

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.get("/")
def list_cameras(user: str = Depends(get_current_user)):
    from main import shared_state
    frame = shared_state.get_latest()
    health = frame.camera_health if frame else {"status": "unknown"}
    return [{"camera_id": "main", "health": health}]


@router.get("/{camera_id}/health")
def get_health(camera_id: str, user: str = Depends(get_current_user)):
    from main import shared_state
    frame = shared_state.get_latest()
    if frame:
        return frame.camera_health
    return {"status": "unknown", "camera_id": camera_id}
