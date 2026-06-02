import unittest

from fastapi.testclient import TestClient

import main
from main import ANSWER_KEYS, QUESTIONS, app


VALID_ANSWERS = {
    "craving": "밥",
    "cuisine": "한식",
    "spice": "매콤",
    "soup": "없음",
    "flavor": "매콤한",
    "main": "돼지",
    "meat_type": "돼지",
    "rice_style": "덮밥",
    "noodle_style": "상관없음",
    "soup_style": "상관없음",
    "snack_style": "상관없음",
    "party_food": "상관없음",
    "dessert_type": "상관없음",
    "cook": "볶음",
    "situation": "혼자",
    "avoid": "없음",
}

KAKAO_ANSWER_SEQUENCE = [
    "밥",
    "매콤",
    "돼지",
    "없음",
    "없음",
]


class TossApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.original_supabase = main.supabase
        main.USER_SESSIONS.clear()
        if hasattr(main, "TOSS_USAGE_EVENTS"):
            main.TOSS_USAGE_EVENTS.clear()
        if hasattr(main, "KAKAO_USAGE_EVENTS"):
            main.KAKAO_USAGE_EVENTS.clear()

    def tearDown(self):
        main.supabase = self.original_supabase

    def post_kakao_skill(self, user_id: str, utterance: str):
        return self.client.post(
            "/kakao/skill",
            json={
                "userRequest": {
                    "utterance": utterance,
                    "user": {
                        "id": user_id,
                    },
                },
            },
        )

    def test_questions_returns_public_question_payload(self):
        response = self.client.get("/api/toss/questions")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], len(QUESTIONS))
        self.assertEqual([item["key"] for item in body["questions"]], ANSWER_KEYS)
        self.assertEqual(body["questions"][0]["key"], "craving")
        self.assertEqual(body["questions"][0]["options"][0]["label"], "밥")
        self.assertNotIn(
            {"value": "치킨피자", "label": "치킨피자"},
            body["questions"][0]["options"],
        )

    def test_recommend_rejects_missing_answers(self):
        response = self.client.post(
            "/api/toss/recommend",
            json={
                "userId": "test-user",
                "answers": {
                    "craving": "밥",
                },
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing answer", response.json()["detail"])

    def test_recommend_rejects_invalid_answer_value(self):
        response = self.client.post(
            "/api/toss/recommend",
            json={
                "userId": "test-user",
                "answers": {
                    **VALID_ANSWERS,
                    "spice": "용암맛",
                },
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid answer", response.json()["detail"])

    def test_recommend_returns_three_recommendations(self):
        response = self.client.post(
            "/api/toss/recommend",
            json={
                "userId": "test-user",
                "answers": VALID_ANSWERS,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["userId"], "test-user")
        self.assertEqual(len(body["recommendations"]), 3)
        self.assertIn("name", body["recommendations"][0])
        self.assertIn("shortDesc", body["recommendations"][0])
        self.assertIn("imageUrl", body["recommendations"][0])

    def test_feedback_choose_saves_action(self):
        response = self.client.post(
            "/api/toss/feedback",
            json={
                "userId": "test-user",
                "menuName": "김치찌개",
                "action": "choose",
                "answers": VALID_ANSWERS,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_feedback_similar_returns_recommendations(self):
        response = self.client.post(
            "/api/toss/feedback",
            json={
                "userId": "test-user",
                "menuName": "김치찌개",
                "action": "similar",
                "answers": VALID_ANSWERS,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["recommendations"]), 3)

    def test_feedback_dislike_excludes_menu(self):
        response = self.client.post(
            "/api/toss/feedback",
            json={
                "userId": "test-user",
                "menuName": "김치찌개",
                "action": "dislike",
                "answers": VALID_ANSWERS,
            },
        )

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.json()["recommendations"]]
        self.assertNotIn("김치찌개", names)

    def test_usage_event_rejects_unknown_event(self):
        response = self.client.post(
            "/api/toss/events",
            json={
                "userId": "test-user",
                "event": "install",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid event", response.json()["detail"])

    def test_usage_metrics_counts_unique_users_and_events(self):
        events = [
            ("u1", "app_open"),
            ("u1", "recommendation_completed"),
            ("u1", "feedback_clicked"),
            ("u1", "share_clicked"),
            ("u2", "app_open"),
            ("u2", "restart_clicked"),
        ]

        for user_id, event in events:
            response = self.client.post(
                "/api/toss/events",
                json={
                    "userId": user_id,
                    "event": event,
                },
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/toss/metrics")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["uniqueUsers"], 2)
        self.assertEqual(body["eventsTotal"], 6)
        self.assertEqual(body["events"]["app_open"], 2)
        self.assertEqual(body["events"]["recommendation_completed"], 1)
        self.assertEqual(body["events"]["feedback_clicked"], 1)
        self.assertEqual(body["events"]["share_clicked"], 1)
        self.assertEqual(body["events"]["restart_clicked"], 1)

    def test_kakao_start_flow_still_works(self):
        response = self.post_kakao_skill("kakao-regression-user", "오늘 뭐 먹지")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["version"], "2.0")

    def test_kakao_question_response_uses_picky_character_card(self):
        response = self.post_kakao_skill("kakao-card-user", "오늘 뭐 먹지")

        self.assertEqual(response.status_code, 200)
        output = response.json()["template"]["outputs"][0]
        card = output["basicCard"]
        self.assertEqual(card["title"], "1. 오늘 당기는 건?")
        self.assertIn("/static/picky/picky-question-card.png", card["thumbnail"]["imageUrl"])
        self.assertIn("1. 밥", card["description"])
        self.assertNotIn("치킨/피자", card["description"])
        self.assertNotIn(
            {"action": "message", "label": "치킨/피자", "messageText": "치킨피자"},
            response.json()["template"]["quickReplies"],
        )

    def test_kakao_quick_reply_labels_are_short_and_still_parse(self):
        user_id = "kakao-short-label-user"
        self.post_kakao_skill(user_id, "오늘 뭐 먹지")

        response = self.post_kakao_skill(user_id, "밥")
        card = response.json()["template"]["outputs"][0]["basicCard"]
        self.assertEqual(card["title"], "2. 매운 정도는?")
        self.assertIn("1. 안매움", card["description"])
        self.assertIn("5. 마라", card["description"])
        self.assertNotIn("덮밥", card["description"])
        quick_replies = response.json()["template"]["quickReplies"]
        self.assertEqual(
            [item["label"] for item in quick_replies],
            ["안매움", "매콤", "얼큰", "매움", "마라"],
        )
        self.assertEqual(
            [item["messageText"] for item in quick_replies],
            ["안매움", "매콤", "얼큰", "매움", "마라"],
        )

        response = self.post_kakao_skill(user_id, "매콤")
        card = response.json()["template"]["outputs"][0]["basicCard"]
        self.assertEqual(card["title"], "3. 메인 재료는?")

    def test_kakao_direct_chicken_request_uses_meat_branch(self):
        response = self.post_kakao_skill("kakao-direct-chicken-user", "치킨 추천")

        self.assertEqual(response.status_code, 200)
        card = response.json()["template"]["outputs"][0]["basicCard"]
        self.assertEqual(card["title"], "3. 조리 방법은?")
        self.assertIn("튀김", [item["messageText"] for item in response.json()["template"]["quickReplies"]])

    def test_kakao_noodle_branch_asks_preference_not_menu_names(self):
        user_id = "kakao-noodle-preference-user"
        self.post_kakao_skill(user_id, "오늘 뭐 먹지")

        response = self.post_kakao_skill(user_id, "면")

        self.assertEqual(response.status_code, 200)
        card = response.json()["template"]["outputs"][0]["basicCard"]
        self.assertEqual(card["title"], "2. 매운 정도는?")
        self.assertNotIn("짜장", card["description"])
        self.assertNotIn("짬뽕", card["description"])
        self.assertNotIn(
            {"action": "message", "label": "짜장", "messageText": "짜장"},
            response.json()["template"]["quickReplies"],
        )

    def test_kakao_snack_branch_asks_preference_not_menu_names(self):
        user_id = "kakao-snack-preference-user"
        self.post_kakao_skill(user_id, "오늘 뭐 먹지")

        response = self.post_kakao_skill(user_id, "분식")

        self.assertEqual(response.status_code, 200)
        card = response.json()["template"]["outputs"][0]["basicCard"]
        self.assertEqual(card["title"], "2. 매운 정도는?")
        self.assertNotIn("떡볶이", card["description"])
        self.assertNotIn("순대", card["description"])
        self.assertNotIn(
            {"action": "message", "label": "떡볶이", "messageText": "떡볶이"},
            response.json()["template"]["quickReplies"],
        )

    def test_kakao_direct_menu_input_finishes_current_survey(self):
        user_id = "kakao-direct-menu-user"
        self.post_kakao_skill(user_id, "오늘 뭐 먹지")
        self.post_kakao_skill(user_id, "분식")

        response = self.post_kakao_skill(user_id, "떡볶이")

        self.assertEqual(response.status_code, 200)
        carousel = response.json()["template"]["outputs"][0]["carousel"]
        self.assertEqual(carousel["items"][0]["title"], "떡볶이")
        self.assertIn("이유:", carousel["items"][0]["description"])

    def test_kakao_adaptive_flow_persists_question_state_with_supabase(self):
        class MemorySupabase:
            def __init__(self):
                self.sessions = {}

            def table(self, name):
                return MemoryTable(self, name)

        class MemoryTable:
            def __init__(self, client, name):
                self.client = client
                self.name = name
                self.user_id = None
                self.payload = None

            def select(self, *_args):
                return self

            def eq(self, _column, value):
                self.user_id = value
                return self

            def upsert(self, payload):
                self.payload = payload
                return self

            def insert(self, _payload):
                return self

            def execute(self):
                if self.name == "user_sessions" and self.payload is not None:
                    self.client.sessions[self.payload["user_id"]] = dict(self.payload)
                    return type("Result", (), {"data": [self.payload]})()
                if self.name == "user_sessions" and self.user_id in self.client.sessions:
                    return type("Result", (), {"data": [self.client.sessions[self.user_id]]})()
                return type("Result", (), {"data": []})()

        main.supabase = MemorySupabase()
        user_id = "kakao-supabase-flow-user"

        self.post_kakao_skill(user_id, "오늘 뭐 먹지")
        self.post_kakao_skill(user_id, "밥")
        response = self.post_kakao_skill(user_id, "매콤")

        card = response.json()["template"]["outputs"][0]["basicCard"]
        self.assertEqual(card["title"], "3. 메인 재료는?")

    def test_kakao_feedback_response_uses_picky_character_card(self):
        user_id = "kakao-feedback-card-user"
        self.post_kakao_skill(user_id, "오늘 뭐 먹지")

        for answer in KAKAO_ANSWER_SEQUENCE:
            self.post_kakao_skill(user_id, answer)

        response = self.post_kakao_skill(user_id, "김치찌개 선택")

        self.assertEqual(response.status_code, 200)
        output = response.json()["template"]["outputs"][0]
        card = output["basicCard"]
        self.assertEqual(card["title"], "아하, 김치찌개로 결정!")
        self.assertIn("/static/picky/picky-aha-card.png", card["thumbnail"]["imageUrl"])

    def test_kakao_recommendation_response_includes_share_quick_reply(self):
        user_id = "kakao-share-reply-user"
        self.post_kakao_skill(user_id, "오늘 뭐 먹지")

        for answer in KAKAO_ANSWER_SEQUENCE:
            response = self.post_kakao_skill(user_id, answer)
            self.assertEqual(response.status_code, 200)

        quick_replies = response.json()["template"]["quickReplies"]
        self.assertIn(
            {"action": "message", "label": "공유", "messageText": "친구에게 공유"},
            quick_replies,
        )
        card = response.json()["template"]["outputs"][0]["carousel"]["items"][0]
        self.assertIn("이유:", card["description"])

    def test_kakao_share_prompt_returns_invite_copy_and_tracks_event(self):
        response = self.post_kakao_skill("kakao-share-user", "친구에게 공유")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        text = body["template"]["outputs"][0]["simpleText"]["text"]
        self.assertIn("Picky", text)
        self.assertIn("피키추천", text)
        self.assertIn("점심추천", text)

        metrics = self.client.get("/api/kakao/metrics").json()
        self.assertEqual(metrics["events"]["kakao_share_prompt"], 1)

    def test_kakao_usage_metrics_counts_funnel_events(self):
        user_id = "kakao-metrics-user"
        response = self.post_kakao_skill(user_id, "오늘 뭐 먹지")
        self.assertEqual(response.status_code, 200)

        for answer in KAKAO_ANSWER_SEQUENCE:
            response = self.post_kakao_skill(user_id, answer)
            self.assertEqual(response.status_code, 200)

        response = self.post_kakao_skill(user_id, "김치찌개 선택")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/kakao/metrics")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["uniqueUsers"], 1)
        self.assertEqual(body["eventsTotal"], 8)
        self.assertEqual(body["events"]["kakao_start"], 1)
        self.assertEqual(body["events"]["kakao_question_answered"], 5)
        self.assertEqual(body["events"]["kakao_recommendation_completed"], 1)
        self.assertEqual(body["events"]["kakao_feedback_clicked"], 1)

    def test_kakao_usage_metrics_counts_restart(self):
        user_id = "kakao-restart-user"
        self.assertEqual(self.post_kakao_skill(user_id, "오늘 뭐 먹지").status_code, 200)
        self.assertEqual(self.post_kakao_skill(user_id, "다시 추천").status_code, 200)

        response = self.client.get("/api/kakao/metrics")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["uniqueUsers"], 1)
        self.assertEqual(body["events"]["kakao_start"], 1)
        self.assertEqual(body["events"]["kakao_restart"], 1)

    def test_kakao_growth_metrics_tracks_campaign_start_keywords(self):
        self.assertEqual(self.post_kakao_skill("kakao-lunch-user", "점심추천").status_code, 200)
        self.assertEqual(self.post_kakao_skill("kakao-dinner-user", "저녁추천").status_code, 200)
        self.assertEqual(self.post_kakao_skill("kakao-organic-user", "오늘 뭐 먹지").status_code, 200)

        response = self.client.get("/api/kakao/growth")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["targetUsers"], 1000)
        self.assertEqual(body["uniqueUsers"], 3)
        self.assertEqual(body["remainingUsers"], 997)
        self.assertEqual(body["campaignStarts"]["threads_lunch"], 1)
        self.assertEqual(body["campaignStarts"]["threads_dinner"], 1)
        self.assertEqual(body["campaignStarts"]["organic"], 1)

    def test_storage_health_reports_memory_fallback_when_supabase_is_missing(self):
        main.supabase = None

        response = self.client.get("/api/ops/storage")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["supabaseConfigured"])
        self.assertEqual(body["metricsPersistence"], "memory_fallback")
        self.assertFalse(body["tables"]["kakao_usage_events"]["ok"])
        self.assertFalse(body["tables"]["toss_usage_events"]["ok"])

    def test_storage_health_reports_supabase_when_usage_tables_are_reachable(self):
        class Query:
            def select(self, _columns):
                return self

            def limit(self, _count):
                return self

            def execute(self):
                class Result:
                    data = []

                return Result()

        class FakeSupabase:
            def table(self, _name):
                return Query()

        main.supabase = FakeSupabase()

        response = self.client.get("/api/ops/storage")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["supabaseConfigured"])
        self.assertEqual(body["metricsPersistence"], "supabase")
        self.assertTrue(body["tables"]["kakao_usage_events"]["ok"])
        self.assertTrue(body["tables"]["toss_usage_events"]["ok"])

    def test_storage_health_marks_only_failing_usage_table(self):
        class Query:
            def __init__(self, should_fail=False):
                self.should_fail = should_fail

            def select(self, _columns):
                return self

            def limit(self, _count):
                return self

            def execute(self):
                if self.should_fail:
                    raise RuntimeError("relation does not exist")

                class Result:
                    data = []

                return Result()

        class FakeSupabase:
            def table(self, name):
                return Query(should_fail=name == "kakao_usage_events")

        main.supabase = FakeSupabase()

        response = self.client.get("/api/ops/storage")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["metricsPersistence"], "memory_fallback")
        self.assertFalse(body["tables"]["kakao_usage_events"]["ok"])
        self.assertIn("relation does not exist", body["tables"]["kakao_usage_events"]["error"])
        self.assertTrue(body["tables"]["toss_usage_events"]["ok"])


if __name__ == "__main__":
    unittest.main()
