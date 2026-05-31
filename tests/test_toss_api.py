import unittest

from fastapi.testclient import TestClient

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


class TossApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

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

    def test_kakao_start_flow_still_works(self):
        response = self.client.post(
            "/kakao/skill",
            json={
                "userRequest": {
                    "utterance": "오늘 뭐 먹지",
                    "user": {
                        "id": "kakao-regression-user",
                    },
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["version"], "2.0")


if __name__ == "__main__":
    unittest.main()
