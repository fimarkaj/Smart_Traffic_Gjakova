"""
db.py — SQLite persistence layer. Extended from original with retention support.
"""

import csv
import json
import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SQL_CREATE = """
CREATE TABLE IF NOT EXISTS rois (
    roi_id    TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    roi_type  TEXT NOT NULL DEFAULT 'main',
    polygon_a TEXT NOT NULL,
    polygon_b TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS counts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_second TEXT    NOT NULL,
    roi_id    TEXT    NOT NULL REFERENCES rois(roi_id),
    car_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE (roi_id, ts_second)
);
CREATE TABLE IF NOT EXISTS crossings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_second      TEXT    NOT NULL,
    roi_id         TEXT    NOT NULL REFERENCES rois(roi_id),
    crossing_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE (roi_id, ts_second)
);
CREATE TABLE IF NOT EXISTS daily_summary (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    day_date        TEXT NOT NULL,
    roi_id          TEXT NOT NULL REFERENCES rois(roi_id),
    total_occupancy INTEGER NOT NULL DEFAULT 0,
    total_crossings INTEGER NOT NULL DEFAULT 0,
    peak_occupancy  INTEGER NOT NULL DEFAULT 0,
    peak_ts         TEXT,
    active_seconds  INTEGER NOT NULL DEFAULT 0,
    UNIQUE (day_date, roi_id)
);
CREATE TABLE IF NOT EXISTS alert_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    roi_id          TEXT,
    metric          TEXT NOT NULL,
    operator        TEXT NOT NULL,
    threshold       REAL NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    channels        TEXT NOT NULL DEFAULT '[]',
    enabled         INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL
);
"""

SQL_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_counts_ts    ON counts    (ts_second);",
    "CREATE INDEX IF NOT EXISTS idx_counts_roi   ON counts    (roi_id);",
    "CREATE INDEX IF NOT EXISTS idx_cross_ts     ON crossings (ts_second);",
    "CREATE INDEX IF NOT EXISTS idx_cross_roi    ON crossings (roi_id);",
    "CREATE INDEX IF NOT EXISTS idx_daily_date   ON daily_summary (day_date);",
]

# ---------------------------------------------------------------------------
# ROI definitions
# ---------------------------------------------------------------------------

def _parse_polygon(s: str) -> list:
    pts = []
    for tok in s.strip().split(";"):
        tok = tok.strip()
        if tok:
            x, y = tok.split(":")
            pts.append([int(x), int(y)])
    return pts


_RAW = [
    ("1",   "Lane 1",       "main",
     "116:393;153:385;153:359;161:343;168:334;177:323;185:315;175:309;153:320;142:326;129:337;124:348;119:360;118:376;116:395",
     "116:643;153:635;153:609;161:593;168:584;177:573;185:565;175:559;153:570;142:576;129:587;124:598;119:610;118:626;116:645"),
    ("2",   "Lane 2",       "main",
     "143:485;197:465;208:486;298:598;215:599;188:556;143:486",
     "143:735;197:715;208:736;298:848;215:849;188:806;143:736"),
    ("3",   "Lane 3",       "main",
     "172:376;218:359;213:331;227:309;200:303;182:328;167:356;167:375",
     "172:626;218:609;213:581;227:559;200:553;182:578;167:606;167:625"),
    ("4",   "Lane 4",       "main",
     "230:458;295:437;355:487;485:592;494:599;396:595;353:562;340:554;313:551;268:501;232:459",
     "230:708;295:687;355:737;485:842;494:849;396:845;353:812;340:804;313:801;268:751;232:709"),
    ("5",   "Lane 5",       "main",
     "410:371;326:385;332:359;408:346;412:372",
     "410:621;326:635;332:609;408:596;412:622"),
    ("6",   "Lane 6",       "main",
     "21:442;78:428;80:415;35:428;30:444",
     "21:692;78:678;80:665;35:678;30:694"),
    ("7",   "Lane 7",       "main",
     "411:394;413:373;328:387;322:406;411:395",
     "411:644;413:623;328:637;322:656;411:645"),
    ("8",   "Lane 8",       "main",
     "1:472;82:467;88:431;2:457;3:472",
     "1:722;82:717;88:681;2:707;3:722"),
]

ROI_DEFINITIONS = [
    {"roi_id": r, "name": n, "roi_type": t,
     "polygon_a": json.dumps(_parse_polygon(a)),
     "polygon_b": json.dumps(_parse_polygon(b))}
    for r, n, t, a, b in _RAW
]

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def open_db(db_path: str = "data/traffic.db") -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA cache_size=-16000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(conn: sqlite3.Connection):
    with conn:
        conn.executescript(SQL_CREATE)
        for idx in SQL_INDEXES:
            conn.execute(idx)
    logger.info("DB schema initialised")


def seed_rois(conn: sqlite3.Connection):
    sql = """INSERT OR IGNORE INTO rois (roi_id, name, roi_type, polygon_a, polygon_b)
             VALUES (:roi_id, :name, :roi_type, :polygon_a, :polygon_b)"""
    with conn:
        conn.executemany(sql, ROI_DEFINITIONS)

# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

def upsert_counts_bulk(conn: sqlite3.Connection, rows: list[dict]):
    if not rows:
        return
    sql = "INSERT OR REPLACE INTO counts (ts_second, roi_id, car_count) VALUES (:ts_second, :roi_id, :car_count)"
    try:
        conn.execute("PRAGMA foreign_keys=OFF;")
        with conn:
            conn.executemany(sql, rows)
    finally:
        conn.execute("PRAGMA foreign_keys=ON;")


def upsert_crossings_bulk(conn: sqlite3.Connection, rows: list[dict]):
    rows = [r for r in rows if r.get("crossing_count", 0) > 0]
    if not rows:
        return
    sql = """INSERT INTO crossings (ts_second, roi_id, crossing_count)
             VALUES (:ts_second, :roi_id, :crossing_count)
             ON CONFLICT(roi_id, ts_second)
             DO UPDATE SET crossing_count = crossing_count + excluded.crossing_count"""
    try:
        conn.execute("PRAGMA foreign_keys=OFF;")
        with conn:
            conn.executemany(sql, rows)
    finally:
        conn.execute("PRAGMA foreign_keys=ON;")

# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def query_counts(conn, start_dt, end_dt, roi_ids=None) -> list[dict]:
    s, e = start_dt.isoformat(timespec="seconds"), end_dt.isoformat(timespec="seconds")
    if roi_ids:
        ph = ",".join("?" * len(roi_ids))
        sql = f"SELECT ts_second, roi_id, car_count FROM counts WHERE ts_second BETWEEN ? AND ? AND roi_id IN ({ph}) ORDER BY ts_second, roi_id"
        params = [s, e] + list(roi_ids)
    else:
        sql = "SELECT ts_second, roi_id, car_count FROM counts WHERE ts_second BETWEEN ? AND ? ORDER BY ts_second, roi_id"
        params = [s, e]
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def query_totals(conn, start_dt, end_dt) -> dict:
    s, e = start_dt.isoformat(timespec="seconds"), end_dt.isoformat(timespec="seconds")
    sql = """
        SELECT r.roi_id, r.name,
               COALESCE(c.total_occupancy, 0) AS total_occupancy,
               COALESCE(x.total_crossings, 0) AS total_crossings
        FROM rois r
        LEFT JOIN (SELECT roi_id, SUM(car_count) AS total_occupancy FROM counts WHERE ts_second BETWEEN ? AND ? GROUP BY roi_id) c ON c.roi_id = r.roi_id
        LEFT JOIN (SELECT roi_id, SUM(crossing_count) AS total_crossings FROM crossings WHERE ts_second BETWEEN ? AND ? GROUP BY roi_id) x ON x.roi_id = r.roi_id
        ORDER BY total_crossings DESC"""
    rows = [dict(r) for r in conn.execute(sql, [s, e, s, e]).fetchall()]
    visible = rows
    return {
        "per_roi":           visible,
        "overall_occupancy": sum(r["total_occupancy"] for r in visible),
        "overall_crossings": sum(r["total_crossings"] for r in visible),
    }


def query_session_info(conn) -> dict:
    row = conn.execute("SELECT MIN(ts_second) AS s, MAX(ts_second) AS e FROM counts").fetchone()
    if not row or not row["s"]:
        return {"session_start": None, "session_end": None, "runtime_seconds": 0}
    fmt = "%Y-%m-%dT%H:%M:%S"
    start = datetime.strptime(row["s"], fmt)
    end   = datetime.strptime(row["e"], fmt)
    return {"session_start": start.strftime("%H:%M:%S"),
            "session_end":   end.strftime("%H:%M:%S"),
            "runtime_seconds": int((end - start).total_seconds())}


def build_daily_summary(conn, day_date: date):
    day_str   = day_date.isoformat()
    start_iso = f"{day_str}T00:00:00"
    end_iso   = f"{day_str}T23:59:59"
    rows = conn.execute("""
        SELECT r.roi_id,
               COALESCE(SUM(c.car_count), 0) AS total_occupancy,
               COALESCE(MAX(c.car_count), 0) AS peak_occupancy,
               COALESCE(COUNT(CASE WHEN c.car_count > 0 THEN 1 END), 0) AS active_seconds,
               COALESCE(SUM(x.crossing_count), 0) AS total_crossings
        FROM rois r
        LEFT JOIN counts c ON c.roi_id = r.roi_id AND c.ts_second BETWEEN ? AND ?
        LEFT JOIN crossings x ON x.roi_id = r.roi_id AND x.ts_second BETWEEN ? AND ?
        GROUP BY r.roi_id
    """, [start_iso, end_iso, start_iso, end_iso]).fetchall()

    upsert_sql = """INSERT OR REPLACE INTO daily_summary
        (day_date, roi_id, total_occupancy, total_crossings, peak_occupancy, peak_ts, active_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?)"""
    summary = []
    for row in rows:
        peak = conn.execute(
            "SELECT ts_second FROM counts WHERE roi_id=? AND ts_second BETWEEN ? AND ? ORDER BY car_count DESC LIMIT 1",
            [row["roi_id"], start_iso, end_iso]
        ).fetchone()
        summary.append((day_str, row["roi_id"], row["total_occupancy"], row["total_crossings"],
                         row["peak_occupancy"], peak["ts_second"] if peak else None, row["active_seconds"]))
    with conn:
        conn.executemany(upsert_sql, summary)


def query_daily_summary(conn, start_date: date, end_date: date) -> list[dict]:
    sql = """SELECT ds.day_date, ds.roi_id, r.name, ds.total_occupancy,
                    ds.peak_occupancy, ds.peak_ts, ds.active_seconds
             FROM daily_summary ds JOIN rois r ON r.roi_id = ds.roi_id
             WHERE ds.day_date BETWEEN ? AND ?
             ORDER BY ds.day_date, ds.total_occupancy DESC"""
    return [dict(r) for r in conn.execute(sql, [start_date.isoformat(), end_date.isoformat()]).fetchall()]


# ---------------------------------------------------------------------------
# Alert rules CRUD
# ---------------------------------------------------------------------------

def get_alert_rules(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM alert_rules ORDER BY id").fetchall()]


def upsert_alert_rule(conn, rule: dict) -> int:
    if rule.get("id"):
        conn.execute("""UPDATE alert_rules SET name=?, roi_id=?, metric=?, operator=?,
                        threshold=?, duration_seconds=?, channels=?, enabled=?
                        WHERE id=?""",
                     [rule["name"], rule.get("roi_id"), rule["metric"], rule["operator"],
                      rule["threshold"], rule.get("duration_seconds", 0),
                      json.dumps(rule.get("channels", [])), int(rule.get("enabled", 1)),
                      rule["id"]])
        return rule["id"]
    else:
        cur = conn.execute("""INSERT INTO alert_rules (name, roi_id, metric, operator,
                              threshold, duration_seconds, channels, enabled, created_at)
                              VALUES (?,?,?,?,?,?,?,?,?)""",
                           [rule["name"], rule.get("roi_id"), rule["metric"], rule["operator"],
                            rule["threshold"], rule.get("duration_seconds", 0),
                            json.dumps(rule.get("channels", [])), 1,
                            datetime.now().isoformat(timespec="seconds")])
        conn.commit()
        return cur.lastrowid


def delete_alert_rule(conn, rule_id: int):
    with conn:
        conn.execute("DELETE FROM alert_rules WHERE id=?", [rule_id])


def sync_default_alert_rules(conn, rules: list[dict]):
    """Create or update startup-defined alert rules by name."""
    if not rules:
        return
    existing = {row["name"]: dict(row) for row in conn.execute("SELECT id, name FROM alert_rules").fetchall()}
    with conn:
        for rule in rules:
            channels = json.dumps(rule.get("channels", []))
            if rule.get("name") in existing:
                conn.execute(
                    """UPDATE alert_rules SET roi_id=?, metric=?, operator=?, threshold=?, duration_seconds=?, channels=?, enabled=? WHERE name=?""",
                    [rule.get("roi_id"), rule["metric"], rule["operator"], rule["threshold"], rule.get("duration_seconds", 0), channels, int(rule.get("enabled", 1)), rule["name"]]
                )
            else:
                conn.execute(
                    """INSERT INTO alert_rules (name, roi_id, metric, operator, threshold, duration_seconds, channels, enabled, created_at)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                    [rule["name"], rule.get("roi_id"), rule["metric"], rule["operator"], rule["threshold"], rule.get("duration_seconds", 0), channels, int(rule.get("enabled", 1)), datetime.now().isoformat(timespec="seconds")]
                )


# ---------------------------------------------------------------------------
# Data retention
# ---------------------------------------------------------------------------

def run_retention(conn, retention_days: int):
    """Delete per-second rows older than retention_days. Keep daily_summary forever."""
    cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat(timespec="seconds")
    with conn:
        c = conn.execute("DELETE FROM counts WHERE ts_second < ?", [cutoff])
        x = conn.execute("DELETE FROM crossings WHERE ts_second < ?", [cutoff])
    logger.info(f"Retention: deleted {c.rowcount} count rows, {x.rowcount} crossing rows older than {cutoff}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def floor_to_second(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat(timespec="seconds")
