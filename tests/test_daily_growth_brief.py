import unittest

from scripts.daily_growth_brief import build_growth_brief, select_focus_campaign


class DailyGrowthBriefTests(unittest.TestCase):
    def test_select_focus_campaign_starts_with_lunch_when_no_campaign_has_data(self):
        campaign = select_focus_campaign(
            {
                "uniqueUsers": 1,
                "campaignStarts": {},
                "events": {"kakao_start": 0},
            }
        )

        self.assertEqual(campaign["key"], "threads_lunch")
        self.assertEqual(campaign["keyword"], "점심추천")

    def test_select_focus_campaign_uses_clear_winning_campaign(self):
        campaign = select_focus_campaign(
            {
                "uniqueUsers": 80,
                "campaignStarts": {
                    "threads_solo": 12,
                    "threads_lunch": 5,
                    "brand": 2,
                },
                "events": {"kakao_start": 19},
            }
        )

        self.assertEqual(campaign["key"], "threads_solo")
        self.assertEqual(campaign["keyword"], "혼밥추천")

    def test_growth_brief_contains_post_replies_video_and_low_completion_action(self):
        brief = build_growth_brief(
            kakao={
                "uniqueUsers": 30,
                "targetUsers": 1000,
                "remainingUsers": 970,
                "progressPercent": 3.0,
                "completionRate": 40.0,
                "feedbackRate": 3.0,
                "campaignStarts": {"threads_lunch": 6},
                "events": {
                    "kakao_start": 10,
                    "kakao_recommendation_completed": 4,
                    "kakao_feedback_clicked": 1,
                    "kakao_share_prompt": 0,
                },
            },
            toss={
                "uniqueUsers": 0,
                "eventsTotal": 0,
                "events": {},
            },
            timestamp="2026-05-31T23:20:00+09:00",
            note="unit-test",
        )

        self.assertIn("Kakao: 30 / 1,000", brief)
        self.assertIn("Focus keyword: `점심추천`", brief)
        self.assertIn("Threads Post", brief)
        self.assertIn("Reply Sprint", brief)
        self.assertIn("Short Video", brief)
        self.assertIn("completion rate is below 55%", brief)
        self.assertIn("Measure Again", brief)

    def test_growth_brief_prioritizes_first_starts_when_no_one_has_started(self):
        brief = build_growth_brief(
            kakao={
                "uniqueUsers": 0,
                "targetUsers": 1000,
                "remainingUsers": 1000,
                "completionRate": 0.0,
                "feedbackRate": 0.0,
                "campaignStarts": {},
                "events": {
                    "kakao_start": 0,
                    "kakao_recommendation_completed": 0,
                    "kakao_feedback_clicked": 0,
                    "kakao_share_prompt": 0,
                },
            },
            toss={
                "uniqueUsers": 0,
                "eventsTotal": 0,
                "events": {},
            },
            timestamp="2026-05-31T23:30:00+09:00",
        )

        self.assertIn("First target: get the first 10 Kakao starts", brief)
        self.assertNotIn("completion rate is below 55%", brief)
        self.assertIn("시작어는 `점심추천`", brief)


if __name__ == "__main__":
    unittest.main()
