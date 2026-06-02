import json
import unittest

from ai_recommendation import parse_ai_turn


class AiRecommendationTests(unittest.TestCase):
    def test_dislike_question_keeps_none_and_removes_escape_duplicates(self):
        turn = parse_ai_turn(
            json.dumps(
                {
                    "action": "ask",
                    "question": "먹기 싫은 건?",
                    "options": ["매운거", "기름진거", "상관없음", "기타", "없음"],
                },
                ensure_ascii=False,
            )
        )

        self.assertEqual(turn["options"], ["매운거", "기름진거", "없음"])

    def test_category_question_keeps_other_instead_of_anything(self):
        turn = parse_ai_turn(
            json.dumps(
                {
                    "action": "ask",
                    "question": "음식 계열은?",
                    "options": ["한식", "중식", "상관없음", "기타"],
                },
                ensure_ascii=False,
            )
        )

        self.assertEqual(turn["options"], ["한식", "중식", "기타"])

    def test_preference_question_keeps_anything_instead_of_other(self):
        turn = parse_ai_turn(
            json.dumps(
                {
                    "action": "ask",
                    "question": "매운 정도는?",
                    "options": ["안매움", "매콤", "기타", "상관없음"],
                },
                ensure_ascii=False,
            )
        )

        self.assertEqual(turn["options"], ["안매움", "매콤", "상관없음"])


if __name__ == "__main__":
    unittest.main()
