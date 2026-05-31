import unittest

from fastapi.testclient import TestClient

import main
from main import ANSWER_KEYS, QUESTIONS, app


VALID_ANSWERS = {
    "situation": "혼밥",
    "meal_goal": "든든한 식사",
    "taste_profile": "매콤",
    "main_ingredient": "고기",
    "form": "밥",
    "spice_level": "매콤",
    "eating_style": "빨리 먹기",
}

KAKAO_ANSWER_SEQUENCE = [
    "혼밥",
    "든든한 식사",
    "매콤",
    "고기",
    "밥",
    "매콤",
    "빨리 먹기",
]


class TossApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        main.USER_SESSIONS.clear()
        if hasattr(main, "TOSS_USAGE_EVENTS"):
            main.TOSS_USAGE_EVENTS.clear()
        if hasattr(main, "KAKAO_USAGE_EVENTS"):
            main.KAKAO_USAGE_EVENTS.clear()

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
        self.assertEqual(body["questions"][0]["options"][0]["label"], "혼밥")

    def test_recommend_rejects_missing_answers(self):
        response = self.client.post(
            "/api/toss/recommend",
            json={
                "userId": "test-user",
                "answers": {
                    "situation": "혼밥",
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
                    "spice_level": "용암맛",
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
        self.assertEqual(card["title"], "1. 누구랑 먹어?")
        self.assertIn("/static/picky/picky-question-card.png", card["thumbnail"]["imageUrl"])
        self.assertEqual(len(response.json()["template"]["quickReplies"]), 5)

    def test_kakao_quick_reply_labels_are_short_and_still_parse(self):
        user_id = "kakao-short-label-user"
        self.post_kakao_skill(user_id, "오늘 뭐 먹지")

        response = self.post_kakao_skill(user_id, "혼밥")
        card = response.json()["template"]["outputs"][0]["basicCard"]
        self.assertEqual(card["title"], "2. 오늘 필요한 느낌은?")
        quick_replies = response.json()["template"]["quickReplies"]
        self.assertEqual(
            [item["label"] for item in quick_replies],
            ["든든", "가볍게", "국물", "매운맛", "새로운"],
        )
        self.assertEqual(
            [item["messageText"] for item in quick_replies],
            ["든든한 식사", "가볍고 깔끔", "속 따뜻한 국물", "스트레스 풀 매운맛", "새로운 메뉴"],
        )

        response = self.post_kakao_skill(user_id, "든든")
        card = response.json()["template"]["outputs"][0]["basicCard"]
        self.assertEqual(card["title"], "3. 맛 방향은?")

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
        self.assertEqual(body["eventsTotal"], 10)
        self.assertEqual(body["events"]["kakao_start"], 1)
        self.assertEqual(body["events"]["kakao_question_answered"], 7)
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


if __name__ == "__main__":
    unittest.main()
