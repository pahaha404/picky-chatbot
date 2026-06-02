import unittest

from delivery_recommendation import (
    DELIVERY_MENUS,
    DELIVERY_QUESTIONS,
    answer_profile_for_menu,
    choose_next_question,
    recommend_delivery_food,
    simulate_profile_winners,
)


class DeliveryRecommendationTests(unittest.TestCase):
    def test_catalog_covers_common_korean_delivery_categories(self):
        names = {menu["name"] for menu in DELIVERY_MENUS}
        categories = {menu["delivery_category"] for menu in DELIVERY_MENUS}

        self.assertGreaterEqual(len(DELIVERY_MENUS), 80)
        self.assertTrue(
            {
                "치킨",
                "중식",
                "피자",
                "분식",
                "족발보쌈",
                "패스트푸드",
                "찜탕찌개",
                "한식",
                "돈까스일식",
                "아시안양식",
                "카페디저트",
            }.issubset(categories)
        )
        self.assertTrue(
            {
                "후라이드치킨",
                "짜장면",
                "피자",
                "떡볶이",
                "족발",
                "햄버거",
                "김치찌개",
                "돈까스",
                "쌀국수",
                "커피",
            }.issubset(names)
        )

    def test_every_menu_can_rank_first_for_its_profile(self):
        winners = simulate_profile_winners()
        dead_menus = [
            menu["name"]
            for menu in DELIVERY_MENUS
            if winners.get(menu["name"], 0) == 0
        ]

        self.assertEqual(dead_menus, [])

    def test_menu_profile_recommends_that_menu_first(self):
        for menu in DELIVERY_MENUS:
            with self.subTest(menu=menu["name"]):
                answers = answer_profile_for_menu(menu)
                recommendations = recommend_delivery_food(answers, limit=3)

                self.assertEqual(recommendations[0]["name"], menu["name"])

    def test_next_question_uses_answer_context(self):
        self.assertEqual(
            choose_next_question({"craving": "밥"}, {"craving"})["key"],
            "rice_style",
        )
        self.assertEqual(
            choose_next_question({"craving": "고기"}, {"craving"})["key"],
            "meat_type",
        )
        self.assertEqual(
            choose_next_question({"craving": "치킨피자"}, {"craving"})["key"],
            "party_food",
        )
        self.assertEqual(
            choose_next_question({"craving": "디저트"}, {"craving"})["key"],
            "dessert_type",
        )

    def test_first_question_stays_on_core_food_shapes(self):
        first_question = next(question for question in DELIVERY_QUESTIONS if question["key"] == "craving")

        self.assertEqual(first_question["options"], ["밥", "면", "국물", "고기", "분식"])

    def test_snack_flow_does_not_ask_cuisine_after_snack_detail(self):
        next_question = choose_next_question(
            {"craving": "분식", "snack_style": "상관없음"},
            {"craving", "snack_style"},
        )

        self.assertNotEqual(next_question["key"], "cuisine")
        self.assertEqual(next_question["key"], "spice")


if __name__ == "__main__":
    unittest.main()
