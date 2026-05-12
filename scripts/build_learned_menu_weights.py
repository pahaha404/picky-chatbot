import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv
from supabase import create_client

import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "learned_menu_weights.json"
MIN_STATISTICAL_FEEDBACK = 300
PYTORCH_READY_FEEDBACK = 1000
SMOOTHING = 8.0
MAX_GLOBAL_WEIGHT = 0.5
MAX_SIGNATURE_WEIGHT = 0.9


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def load_feedback_rows(limit: int) -> List[Dict[str, Any]]:
    load_dotenv(PROJECT_ROOT / ".env.local")
    load_dotenv(PROJECT_ROOT / ".env")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set.")

    client = create_client(supabase_url, supabase_key)
    result = (
        client.table("menu_feedback")
        .select("user_id, menu_name, action, answers, answer_signature")
        .limit(limit)
        .execute()
    )
    return result.data or []


def dedupe_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped = []
    seen = set()

    for index, row in enumerate(rows):
        signature = row.get("answer_signature") or main.answer_signature(row.get("answers") or {})
        key = (
            row.get("user_id") or f"anonymous-{index}",
            row.get("menu_name"),
            row.get("action"),
            signature,
        )

        if key in seen:
            continue

        seen.add(key)
        row["answer_signature"] = signature
        deduped.append(row)

    return deduped


def build_weights(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid_rows = [row for row in dedupe_rows(rows) if main.is_valid_feedback_record(row)]
    global_counts: Dict[str, Dict[str, float]] = defaultdict(lambda: {"choose": 0.0, "dislike": 0.0})
    signature_counts: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: {"choose": 0.0, "dislike": 0.0})
    )

    for row in valid_rows:
        action = row["action"]
        if action not in {"choose", "dislike"}:
            continue

        menu_name = row["menu_name"]
        signature = row["answer_signature"]
        global_counts[menu_name][action] += 1.0
        signature_counts[signature][menu_name][action] += 1.0

    global_weights = {}
    for menu_name, counts in global_counts.items():
        total = counts["choose"] + counts["dislike"]
        if total < 10:
            continue

        net = counts["choose"] - counts["dislike"]
        global_weights[menu_name] = round(
            clamp((net / (total + SMOOTHING)) * MAX_GLOBAL_WEIGHT, -MAX_GLOBAL_WEIGHT, MAX_GLOBAL_WEIGHT),
            4,
        )

    by_signature = {}
    for signature, menu_counts in signature_counts.items():
        signature_weights = {}

        for menu_name, counts in menu_counts.items():
            total = counts["choose"] + counts["dislike"]
            if total < 5:
                continue

            net = counts["choose"] - counts["dislike"]
            signature_weights[menu_name] = round(
                clamp(
                    (net / (total + SMOOTHING)) * MAX_SIGNATURE_WEIGHT,
                    -MAX_SIGNATURE_WEIGHT,
                    MAX_SIGNATURE_WEIGHT,
                ),
                4,
            )

        if signature_weights:
            by_signature[signature] = signature_weights

    return {
        "metadata": {
            "valid_feedback_count": len(valid_rows),
            "min_statistical_feedback": MIN_STATISTICAL_FEEDBACK,
            "pytorch_ready_feedback": PYTORCH_READY_FEEDBACK,
            "model_type": "statistical_weights",
        },
        "global": global_weights,
        "by_signature": by_signature,
    }


def main_cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    rows = load_feedback_rows(limit=args.limit)
    weights = build_weights(rows)
    valid_count = weights["metadata"]["valid_feedback_count"]

    if valid_count < MIN_STATISTICAL_FEEDBACK and not args.force:
        print(
            f"Not enough valid feedback yet: {valid_count}/{MIN_STATISTICAL_FEEDBACK}. "
            "No weights file was written. Use --force only for local testing."
        )
        return

    OUTPUT_PATH.write_text(json.dumps(weights, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Valid feedback: {valid_count}")

    if valid_count < PYTORCH_READY_FEEDBACK:
        print(f"PyTorch training should wait until about {PYTORCH_READY_FEEDBACK} valid feedback rows.")
    else:
        print("Feedback volume is ready for a separate PyTorch offline training script.")


if __name__ == "__main__":
    main_cli()
