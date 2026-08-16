from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from auth import get_current_user

router = APIRouter(prefix="/api/clips", tags=["clips"])


@router.get("/")
def list_clips(user: str = Depends(get_current_user)):
    from main import clip_recorder
    return clip_recorder.list_clips()


@router.get("/{filename}")
def get_clip(filename: str, user: str = Depends(get_current_user)):
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "detector"))
    from config_loader import cfg, resolve_path
    clips_dir = resolve_path(cfg["clips"]["output_dir"])
    path = clips_dir / filename
    if not path.exists() or not path.suffix == ".mp4":
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(str(path), media_type="video/mp4")


@router.delete("/{filename}")
def delete_clip(filename: str, user: str = Depends(get_current_user)):
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "detector"))
    from config_loader import cfg, resolve_path
    clips_dir = resolve_path(cfg["clips"]["output_dir"])
    path = clips_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Clip not found")
    path.unlink()
    return {"status": "deleted", "filename": filename}

