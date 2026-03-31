from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertRule(BaseModel):
    id: Optional[int] = None
    name: str
    roi_id: Optional[str] = None
    metric: str                 # "occupancy" | "crossings_total" | "global_unique"
    operator: str               # ">" | ">=" | "<" | "<=" | "=="
    threshold: float
    duration_seconds: int = 0
    channels: list[str] = []    # ["email", "telegram", "webhook"]
    enabled: bool = True


@router.get("/")
def list_rules(user: str = Depends(get_current_user)):
    from main import db_conn
    from db import get_alert_rules
    return get_alert_rules(db_conn)


@router.post("/")
def create_rule(rule: AlertRule, user: str = Depends(get_current_user)):
    from main import db_conn
    from db import upsert_alert_rule
    new_id = upsert_alert_rule(db_conn, rule.dict())
    return {"status": "created", "id": new_id}


@router.put("/{rule_id}")
def update_rule(rule_id: int, rule: AlertRule, user: str = Depends(get_current_user)):
    from main import db_conn
    from db import upsert_alert_rule
    rule.id = rule_id
    upsert_alert_rule(db_conn, rule.dict())
    return {"status": "updated", "id": rule_id}


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, user: str = Depends(get_current_user)):
    from main import db_conn
    from db import delete_alert_rule
    delete_alert_rule(db_conn, rule_id)
    return {"status": "deleted", "id": rule_id}
