"""
alert_engine.py — Monitors live state and fires alerts when rules are met.
Runs as a background task inside FastAPI.
"""
import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db import get_alert_rules

logger = logging.getLogger(__name__)


class AlertEngine:
    def __init__(self, db_conn, shared_state):
        self._conn  = db_conn
        self._state = shared_state
        # {rule_id: last_fired_ts}
        self._last_fired: dict[int, float] = {}
        # {rule_id: first_triggered_ts} — for duration-based rules
        self._triggered_since: dict[int, float] = {}

    async def run(self):
        """Background loop — checks rules every second."""
        logger.info("Alert engine started")
        while True:
            await asyncio.sleep(1)
            try:
                self._check_rules()
            except Exception as exc:
                logger.error(f"Alert engine error: {exc}", exc_info=True)

    def _check_rules(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from db import get_alert_rules
        import importlib, sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent.parent.parent / "detector"))
        from config_loader import cfg

        rules = get_alert_rules(self._conn)
        frame = self._state.get_latest()
        if frame is None:
            return

        cooldown = cfg["alerts"]["cooldown_seconds"]
        now = time.time()

        for rule in rules:
            if not rule["enabled"]:
                continue

            rid = rule["id"]
            value = self._get_metric(frame, rule)
            if value is None:
                continue

            triggered = self._evaluate(value, rule["operator"], rule["threshold"])

            if triggered:
                if rid not in self._triggered_since:
                    self._triggered_since[rid] = now

                duration_met = (now - self._triggered_since[rid]) >= rule["duration_seconds"]

                if duration_met:
                    last = self._last_fired.get(rid, 0)
                    if now - last >= cooldown:
                        self._last_fired[rid] = now
                        self._fire(rule, value)
            else:
                self._triggered_since.pop(rid, None)

    def _get_metric(self, frame, rule) -> float | None:
        metric  = rule["metric"]
        roi_id  = rule.get("roi_id")

        if metric == "occupancy":
            if roi_id:
                # Match by roi_id — need to find roi name
                # For simplicity, try both roi_id and name as key
                counts = frame.roi_counts
                val = counts.get(roi_id)
                if val is None:
                    # try matching by position
                    for k, v in counts.items():
                        if str(k) == str(roi_id):
                            return float(v)
                return float(val) if val is not None else None
            return float(frame.total_cars)

        if metric == "crossings_total":
            return float(frame.overall_crossings)

        if metric == "global_unique":
            return float(frame.global_unique)

        return None

    def _evaluate(self, value: float, operator: str, threshold: float) -> bool:
        return {
            ">":  value >  threshold,
            ">=": value >= threshold,
            "<":  value <  threshold,
            "<=": value <= threshold,
            "==": value == threshold,
        }.get(operator, False)

    def _fire(self, rule: dict, value: float):
        channels = json.loads(rule.get("channels") or "[]")
        message = (
            f"🚨 Alert: {rule['name']}\n"
            f"Metric: {rule['metric']} {rule['operator']} {rule['threshold']}\n"
            f"Current value: {value:.1f}"
        )
        logger.warning(f"ALERT FIRED — {message}")

        for channel in channels:
            try:
                if channel == "email":
                    self._notify_email(message, rule["name"])
                elif channel == "telegram":
                    asyncio.create_task(self._notify_telegram(message))
                elif channel == "webhook":
                    asyncio.create_task(self._notify_webhook(message, rule))
            except Exception as exc:
                logger.error(f"Alert notification failed ({channel}): {exc}")

    def _notify_email(self, message: str, subject: str):
        import smtplib
        from email.mime.text import MIMEText
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "detector"))
        from config_loader import cfg
        ec = cfg["alerts"]["channels"]["email"]
        if not ec["enabled"]:
            return
        msg = MIMEText(message)
        msg["Subject"] = f"Smart Traffic Alert: {subject}"
        msg["From"]    = ec["from"]
        msg["To"]      = ", ".join(ec["to"])
        with smtplib.SMTP(ec["smtp_host"], ec["smtp_port"]) as s:
            s.starttls()
            s.login(ec["username"], ec["password"])
            s.send_message(msg)
        logger.info("Alert email sent")

    async def _notify_telegram(self, message: str):
        import httpx
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "detector"))
        from config_loader import cfg
        tc = cfg["alerts"]["channels"]["telegram"]
        if not tc["enabled"]:
            return
        url = f"https://api.telegram.org/bot{tc['bot_token']}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": tc["chat_id"], "text": message})
        logger.info("Alert Telegram message sent")

    async def _notify_webhook(self, message: str, rule: dict):
        import httpx
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "detector"))
        from config_loader import cfg
        wc = cfg["alerts"]["channels"]["webhook"]
        if not wc["enabled"]:
            return
        payload = {"content": message}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(wc["url"], json=payload)
            resp.raise_for_status()
        logger.info("Alert webhook sent")
