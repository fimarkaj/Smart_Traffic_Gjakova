import shutil
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pathlib import Path
from auth import get_current_user

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/status")
def model_status(user: str = Depends(get_current_user)):
    from main import model_manager
    return model_manager.get_status()


@router.post("/swap")
async def swap_model(
    file: UploadFile = File(...),
    user: str = Depends(get_current_user),
):
    """Upload a new .pt file to hot-swap the model without restarting."""
    if not file.filename.endswith(".pt"):
        raise HTTPException(status_code=400, detail="Only .pt files accepted")

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "detector"))
    from config_loader import cfg
    swap_dir = Path(cfg["model"]["hot_swap_dir"])
    swap_dir.mkdir(parents=True, exist_ok=True)

    dest = swap_dir / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # ModelManager watcher will pick it up within POLL_INTERVAL seconds
    return {"status": "uploaded", "filename": file.filename,
            "message": "Model will be loaded within 5 seconds"}
