import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


DEFAULT_BASE_URL = "https://picky-chatbot-production.up.railway.app"
DEFAULT_OUTPUT = Path("docs/growth-metrics-log.csv")

GROWTH_SNAPSHOT_FIELDS = [
    "timestamp",
    "note",
    "kakao_unique_users",
    "kakao_target_users",
    "kakao_remaining_users",
    "kakao_progress_percent",
    "kakao_starts",
    "kakao_completions",
    "kakao_feedback_clicks",
    "kakao_share_prompts",
    "kakao_completion_rate",
    "kakao_feedback_rate",
    "kakao_campaign_starts",
    "toss_unique_users",
    "toss_events_total",
    "toss_app_opens",
    "toss_completions",
    "toss_shares",
]


def metric_number(value: Any, default: int | float = 0) -> Any:
    return default if value is None else value


def format_campaign_starts(campaigns: dict[str, Any] | None) -> str:
    if not campaigns:
        return ""

    items = sorted(campaigns.items(), key=lambda item: (-int(item[1]), item[0]))
    return ";".join(f"{name}={count}" for name, count in items)


def build_snapshot_row(
    kakao: dict[str, Any],
    toss: dict[str, Any],
    timestamp: str,
    note: str = "",
) -> dict[str, Any]:
    kakao_events = kakao.get("events") or {}
    toss_events = toss.get("events") or {}

    return {
        "timestamp": timestamp,
        "note": note,
        "kakao_unique_users": metric_number(kakao.get("uniqueUsers")),
        "kakao_target_users": metric_number(kakao.get("targetUsers")),
        "kakao_remaining_users": metric_number(kakao.get("remainingUsers")),
        "kakao_progress_percent": metric_number(kakao.get("progressPercent")),
        "kakao_starts": metric_number(kakao_events.get("kakao_start")),
        "kakao_completions": metric_number(kakao_events.get("kakao_recommendation_completed")),
        "kakao_feedback_clicks": metric_number(kakao_events.get("kakao_feedback_clicked")),
        "kakao_share_prompts": metric_number(kakao_events.get("kakao_share_prompt")),
        "kakao_completion_rate": metric_number(kakao.get("completionRate")),
        "kakao_feedback_rate": metric_number(kakao.get("feedbackRate")),
        "kakao_campaign_starts": format_campaign_starts(kakao.get("campaignStarts")),
        "toss_unique_users": metric_number(toss.get("uniqueUsers")),
        "toss_events_total": metric_number(toss.get("eventsTotal")),
        "toss_app_opens": metric_number(toss_events.get("app_open")),
        "toss_completions": metric_number(toss_events.get("recommendation_completed")),
        "toss_shares": metric_number(toss_events.get("share_clicked")),
    }


def fetch_json(url: str) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc


def append_snapshot(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0

    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=GROWTH_SNAPSHOT_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in GROWTH_SNAPSHOT_FIELDS})


def current_timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append Picky growth metrics to a CSV snapshot log.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="CSV output path")
    parser.add_argument("--note", default="", help="Optional note for this snapshot")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    base_url = args.base_url.rstrip("/")
    kakao = fetch_json(f"{base_url}/api/kakao/growth")
    toss = fetch_json(f"{base_url}/api/toss/metrics")
    row = build_snapshot_row(kakao, toss, current_timestamp(), args.note)
    output = Path(args.output)
    append_snapshot(output, row)
    print(f"Snapshot appended to {output}")
    print(f"Kakao: {row['kakao_unique_users']} / {row['kakao_target_users']} users")
    print(f"Toss: {row['toss_unique_users']} users")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
