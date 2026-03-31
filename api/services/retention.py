"""
retention.py — Scheduled data retention job.
Runs nightly at the configured hour, deletes old per-second rows.
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RetentionScheduler:
    def __init__(self, db_conn):
        self._conn = db_conn

    async def run(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "detector"))
        from config_loader import cfg
        db_cfg = cfg["database"]
        run_hour      = db_cfg.get("retention_run_hour", 3)
        retention_days = db_cfg.get("retention_days", 30)

        logger.info(f"Retention scheduler started — runs at {run_hour:02d}:00, keeps {retention_days} days")

        while True:
            now  = datetime.now()
            next_run_hour = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
            if now >= next_run_hour:
                from datetime import timedelta
                next_run_hour += timedelta(days=1)

            wait_seconds = (next_run_hour - now).total_seconds()
            logger.info(f"Next retention run in {wait_seconds/3600:.1f} hours")
            await asyncio.sleep(wait_seconds)

            try:
                from db import run_retention, build_daily_summary
                # Build daily summary for yesterday before pruning
                yesterday = (datetime.now().date().__class__.today().__class__.fromordinal(
                    datetime.now().toordinal() - 1
                ))
                build_daily_summary(self._conn, yesterday)
                run_retention(self._conn, retention_days)
            except Exception as exc:
                logger.error(f"Retention job failed: {exc}", exc_info=True)
