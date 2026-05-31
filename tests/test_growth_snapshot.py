import csv
import tempfile
import unittest
from pathlib import Path

from scripts.log_growth_snapshot import (
    GROWTH_SNAPSHOT_FIELDS,
    append_snapshot,
    build_snapshot_row,
    format_campaign_starts,
)


class GrowthSnapshotTests(unittest.TestCase):
    def test_format_campaign_starts_orders_by_count_then_name(self):
        campaigns = {
            "threads_dinner": 2,
            "threads_lunch": 5,
            "brand": 2,
        }

        self.assertEqual(format_campaign_starts(campaigns), "threads_lunch=5;brand=2;threads_dinner=2")

    def test_build_snapshot_row_combines_kakao_and_toss_metrics(self):
        row = build_snapshot_row(
            kakao={
                "uniqueUsers": 12,
                "targetUsers": 1000,
                "remainingUsers": 988,
                "progressPercent": 1.2,
                "completionRate": 62.5,
                "feedbackRate": 10.0,
                "campaignStarts": {"threads_lunch": 8, "brand": 4},
                "events": {
                    "kakao_start": 14,
                    "kakao_recommendation_completed": 10,
                    "kakao_feedback_clicked": 1,
                    "kakao_share_prompt": 2,
                },
            },
            toss={
                "uniqueUsers": 3,
                "eventsTotal": 7,
                "events": {
                    "app_open": 3,
                    "recommendation_completed": 2,
                    "share_clicked": 1,
                },
            },
            timestamp="2026-05-31T21:30:00+09:00",
            note="day1",
        )

        self.assertEqual(row["timestamp"], "2026-05-31T21:30:00+09:00")
        self.assertEqual(row["note"], "day1")
        self.assertEqual(row["kakao_unique_users"], 12)
        self.assertEqual(row["kakao_completion_rate"], 62.5)
        self.assertEqual(row["kakao_campaign_starts"], "threads_lunch=8;brand=4")
        self.assertEqual(row["kakao_share_prompts"], 2)
        self.assertEqual(row["toss_unique_users"], 3)
        self.assertEqual(row["toss_shares"], 1)

    def test_append_snapshot_writes_header_once_and_appends_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "growth.csv"
            row = {field: "" for field in GROWTH_SNAPSHOT_FIELDS}
            row["timestamp"] = "2026-05-31T21:30:00+09:00"
            row["kakao_unique_users"] = 12

            append_snapshot(path, row)
            append_snapshot(path, {**row, "timestamp": "2026-05-31T22:00:00+09:00"})

            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["timestamp"], "2026-05-31T21:30:00+09:00")
        self.assertEqual(rows[1]["timestamp"], "2026-05-31T22:00:00+09:00")
        self.assertEqual(rows[0]["kakao_unique_users"], "12")


if __name__ == "__main__":
    unittest.main()
