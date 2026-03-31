from datetime import date, datetime, time
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import io
import csv

from auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _get_db():
    from main import db_conn
    return db_conn


@router.get("/counts")
def get_counts(
    start: datetime = Query(default=None),
    end:   datetime = Query(default=None),
    roi_ids: list[str] = Query(default=None),
    user: str = Depends(get_current_user),
):
    from db import query_counts
    if not start:
        start = datetime.combine(date.today(), time.min)
    if not end:
        end = datetime.combine(date.today(), time.max)
    return query_counts(_get_db(), start, end, roi_ids or None)


@router.get("/totals")
def get_totals(
    start: datetime = Query(default=None),
    end:   datetime = Query(default=None),
    user: str = Depends(get_current_user),
):
    from db import query_totals
    if not start:
        start = datetime.combine(date.today(), time.min)
    if not end:
        end = datetime.combine(date.today(), time.max)
    return query_totals(_get_db(), start, end)


@router.get("/session")
def get_session(user: str = Depends(get_current_user)):
    from db import query_session_info
    return query_session_info(_get_db())


@router.get("/summary")
def get_summary(
    start_date: date = Query(default=None),
    end_date:   date = Query(default=None),
    user: str = Depends(get_current_user),
):
    from db import query_daily_summary
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today()
    return query_daily_summary(_get_db(), start_date, end_date)


@router.post("/summary/build")
def build_summary(
    day: date = Query(default=None),
    user: str = Depends(get_current_user),
):
    from db import build_daily_summary
    if not day:
        day = date.today()
    build_daily_summary(_get_db(), day)
    return {"status": "ok", "day": str(day)}


@router.get("/export/csv")
def export_csv(
    start: datetime = Query(default=None),
    end:   datetime = Query(default=None),
    user: str = Depends(get_current_user),
):
    from db import query_counts
    if not start:
        start = datetime.combine(date.today(), time.min)
    if not end:
        end = datetime.combine(date.today(), time.max)
    rows = query_counts(_get_db(), start, end)

    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=counts_{date.today()}.csv"}
    )


@router.get("/export/sumo")
def export_sumo(
    output: str = Query(default="sumo_output/traffic_state.csv"),
    user: str = Depends(get_current_user),
):
    from db import query_totals
    from datetime import time as dtime
    start = datetime.combine(date.today(), dtime.min)
    end   = datetime.combine(date.today(), dtime.max)
    totals = query_totals(_get_db(), start, end)

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from sumo_csv_export import export_sumo_csv_from_db_totals
    path = export_sumo_csv_from_db_totals(totals["per_roi"], output)
    return {"status": "ok", "path": path}
