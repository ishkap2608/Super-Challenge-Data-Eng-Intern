import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any

import pandas as pd

logger = logging.getLogger("events_pipeline")


@dataclass
class ProcessResult:
    sessions_df: pd.DataFrame
    skipped_df: pd.DataFrame
    events_df: pd.DataFrame
    stats: dict[str, Any]


def _parse_iso8601(s: Any) -> datetime:
    if not isinstance(s, str):
        raise ValueError("event_time not a string")

    txt = s.strip()
    if not txt:
        raise ValueError("event_time empty")

    # Normalize common UTC suffix "Z" for older Python compatibility
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(txt)
    except Exception as e:
        raise ValueError(f"invalid ISO-8601: {e}")

    # If naive, assume UTC (pragmatic for take-home)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def _extract_events_from_content(content: str) -> list[tuple[int, str]]:
    """Extract individual event objects {} from JSON content, tracking their position."""
    events = []
    event_index = 0
    depth = 0
    start = -1
    
    for i, char in enumerate(content):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start != -1:
                event_str = content[start:i+1]
                event_index += 1
                events.append((event_index, event_str))
                start = -1
    
    return events


def process_file(fp: IO[bytes]) -> ProcessResult:
    valid_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []

    try:
        content = fp.read().decode("utf-8", errors="replace")
    except Exception:
        content = str(fp.read())

    # Extract each event object {} independently
    events = _extract_events_from_content(content)
    total_events = len(events)

    for event_no, event_str in events:
        try:
            obj = json.loads(event_str)
        except Exception as e:
            reason = f"json_decode_error: {e}"
            logger.warning("skip event=%d reason=%s", event_no, reason)
            skipped_rows.append({"event": event_no, "reason": reason, "raw": event_str[:300]})
            continue

        try:
            user_id = obj["user_id"]
            event_time = obj["event_time"]
            event_type = obj["event_type"]
        except Exception as e:
            reason = f"missing_key_or_bad_schema: {e}"
            logger.warning("skip event=%d reason=%s", event_no, reason)
            skipped_rows.append({"event": event_no, "reason": reason, "raw": event_str[:300]})
            continue

        try:
            dt = _parse_iso8601(event_time)
        except Exception as e:
            reason = str(e)
            logger.warning("skip event=%d reason=%s", event_no, reason)
            skipped_rows.append({
                "event": event_no,
                "reason": reason,
                "user_id": user_id,
                "event_time": event_time,
                "event_type": event_type,
            })
            continue

        valid_rows.append({
            "user_id": int(user_id),
            "event_time": dt,
            "event_type": str(event_type),
            "event_index": event_no,
        })

    events_df = pd.DataFrame(valid_rows)
    skipped_df = pd.DataFrame(skipped_rows)

    if events_df.empty:
        sessions_df = pd.DataFrame(columns=["user_id", "session_start", "session_end", "event_count"])
        stats = {
            "total_events": total_events,
            "valid_events": 0,
            "skipped_events": len(skipped_df),
            "duplicates_removed": 0,
            "unique_users": 0,
        }
        return ProcessResult(sessions_df, skipped_df, events_df, stats)

    # Normalize to pandas datetime (UTC)
    events_df["event_time"] = pd.to_datetime(events_df["event_time"], utc=True)

    before = len(events_df)
    events_df = events_df.drop_duplicates(subset=["user_id", "event_time", "event_type"], keep="first").reset_index(drop=True)
    dupes_removed = before - len(events_df)

    sessions_df = (
        events_df.groupby("user_id", as_index=False)
        .agg(
            session_start=("event_time", "min"),
            session_end=("event_time", "max"),
            event_count=("event_time", "size"),
        )
        .sort_values("user_id")
        .reset_index(drop=True)
    )

    # Make timestamps pretty / portable
    sessions_df["session_start"] = sessions_df["session_start"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    sessions_df["session_end"] = sessions_df["session_end"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    stats = {
        "total_events": total_events,
        "valid_events": len(valid_rows),
        "skipped_events": len(skipped_df),
        "duplicates_removed": int(dupes_removed),
        "unique_users": int(events_df["user_id"].nunique()),
    }

    return ProcessResult(sessions_df, skipped_df, events_df, stats)


def process_path(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with path.open("rb") as f:
        res = process_file(f)
    return res.sessions_df, res.skipped_df, res.stats
