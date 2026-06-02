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
            "spice",
        )
        self.assertEqual(
            choose_next_question({"craving": "고기"}, {"craving"})["key"],
            "main",
        )
        self.assertEqual(
            choose_next_question({"craving": "치킨피자"}, {"craving"})["key"],
            "situation",
        )
        self.assertEqual(
            choose_next_question({"craving": "디저트"}, {"craving"})["key"],
            "flavor",
        )

    def test_food_shape_branches_do_not_ask_menu_subtype_questions(self):
        forbidden_next_keys = {
            "밥": "rice_style",
            "면": "noodle_style",
            "국물": "soup_style",
            "고기": "meat_type",
            "분식": "snack_style",
        }

        for craving, forbidden_key in forbidden_next_keys.items():
            with self.subTest(craving=craving):
                next_question = choose_next_question({"craving": craving}, {"craving"})

                self.assertNotEqual(next_question["key"], forbidden_key)

    def test_first_question_stays_on_core_food_shapes(self):
        first_question = next(question for question in DELIVERY_QUESTIONS if question["key"] == "craving")

        self.assertEqual(first_question["options"], ["밥", "면", "국물", "고기", "분식", "기타", "상관없음"])

    def test_escape_options_are_available_where_needed(self):
        question_by_key = {question["key"]: question for question in DELIVERY_QUESTIONS}

        for key in ("craving", "cuisine", "soup", "flavor", "main", "cook", "situation"):
            with self.subTest(key=key, option="기타"):
                self.assertIn("기타", question_by_key[key]["options"])

        for key in ("craving", "cuisine", "spice", "soup", "flavor", "main", "cook", "situation"):
            with self.subTest(key=key, option="상관없음"):
                self.assertIn("상관없음", question_by_key[key]["options"])

        self.assertIn("기타", question_by_key["avoid"]["options"])
        self.assertIn("없음", question_by_key["avoid"]["options"])

    def test_other_and_anything_top_level_answers_use_broad_route(self):
        self.assertEqual(
            choose_next_question({"craving": "기타"}, {"craving"})["key"],
            "spice",
        )
        self.assertEqual(
            choose_next_question({"craving": "상관없음"}, {"craving"})["key"],
            "spice",
        )

    def test_snack_flow_does_not_ask_cuisine_after_snack_detail(self):
        next_question = choose_next_question(
            {"craving": "분식", "snack_style": "상관없음"},
            {"craving", "snack_style"},
        )

        self.assertNotEqual(next_question["key"], "cuisine")
        self.assertEqual(next_question["key"], "spice")

    def test_noodle_and_snack_branches_ask_preference_not_menu_names(self):
        self.assertEqual(
            choose_next_question({"craving": "면"}, {"craving"})["key"],
            "spice",
        )
        self.assertEqual(
            choose_next_question({"craving": "분식"}, {"craving"})["key"],
            "spice",
        )

    def test_branch_routes_do_not_fall_back_to_common_cuisine_order(self):
        self.assertEqual(
            choose_next_question(
                {"craving": "밥", "spice": "매콤"},
                {"craving", "spice"},
            )["key"],
            "main",
        )
        self.assertEqual(
            choose_next_question(
                {"craving": "고기", "main": "닭"},
                {"craving", "main"},
            )["key"],
            "cook",
        )
        self.assertEqual(
            choose_next_question(
                {"craving": "분식", "snack_style": "떡볶이"},
                {"craving", "snack_style"},
            )["key"],
            "spice",
        )

    def test_chicken_can_be_reached_from_meat_branch(self):
        recommendations = recommend_delivery_food(
            {
                "craving": "고기",
                "meat_type": "닭",
                "cook": "튀김",
                "situation": "야식",
                "spice": "안매움",
            },
            limit=3,
        )

        self.assertEqual(recommendations[0]["name"], "후라이드치킨")

    def test_recommendation_reason_explains_matched_branch(self):
        recommendations = recommend_delivery_food(
            {
                "craving": "밥",
                "rice_style": "덮밥",
                "spice": "매콤",
                "main": "돼지",
                "avoid": "없음",
            },
            limit=1,
        )

        self.assertIn("reason", recommendations[0])
        self.assertIn("덮밥", recommendations[0]["reason"])
        self.assertIn("매콤", recommendations[0]["reason"])

    def test_anything_answer_is_neutral_in_scoring(self):
        base = recommend_delivery_food({"craving": "분식"}, limit=3)
        neutral = recommend_delivery_food(
            {"craving": "분식", "main": "상관없음"},
            limit=3,
        )

        self.assertEqual(
            [item["name"] for item in neutral],
            [item["name"] for item in base],
        )
        self.assertNotIn("상관없음", neutral[0]["reason"])


if __name__ == "__main__":
    unittest.main()
