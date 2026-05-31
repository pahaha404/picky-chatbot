import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from supabase import Client, create_client


load_dotenv()
load_dotenv(".env.local", override=False)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

USER_SESSIONS: Dict[str, Dict[str, Any]] = {}
MENU_FEEDBACK: List[Dict[str, Any]] = []
TOSS_USAGE_EVENTS: List[Dict[str, Any]] = []
TOSS_USAGE_EVENT_NAMES = {
    "app_open",
    "questions_loaded",
    "recommendation_completed",
    "feedback_clicked",
    "share_clicked",
    "restart_clicked",
}

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://picky-chatbot-production.up.railway.app").rstrip("/")
LEARNED_MENU_WEIGHTS_PATH = os.getenv("LEARNED_MENU_WEIGHTS_PATH", "learned_menu_weights.json")
FOOD_IMAGE_BASE_URL = os.getenv("FOOD_IMAGE_BASE_URL", "").rstrip("/")
TOSS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "TOSS_ALLOWED_ORIGINS",
        ",".join(
            [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "https://picky-menu.apps.tossmini.com",
                "https://picky-menu.private-apps.tossmini.com",
            ]
        ),
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=TOSS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("WARNING: Supabase environment variables are not set.")


def load_learned_menu_weights() -> Dict[str, Any]:
    if not os.path.exists(LEARNED_MENU_WEIGHTS_PATH):
        return {}

    try:
        with open(LEARNED_MENU_WEIGHTS_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"WARNING: Failed to load learned menu weights: {exc}")
        return {}


LEARNED_MENU_WEIGHTS = load_learned_menu_weights()


# ---------------------------------------------------------
# Question flow
# ---------------------------------------------------------
QUESTIONS = [
    {
        "key": "situation",
        "text": "오늘 누구랑 먹어?",
        "options": {
            "1": "혼밥",
            "2": "친구랑",
            "3": "데이트",
            "4": "가족·동료",
            "5": "야식",
        },
    },
    {
        "key": "meal_goal",
        "text": "오늘 음식이 해줬으면 하는 역할은?",
        "options": {
            "1": "든든한 식사",
            "2": "가볍고 깔끔",
            "3": "속 따뜻한 국물",
            "4": "스트레스 풀 매운맛",
            "5": "새로운 메뉴",
        },
    },
    {
        "key": "taste_profile",
        "text": "맛의 방향은?",
        "options": {
            "1": "매콤",
            "2": "담백",
            "3": "고소·크리미",
            "4": "새콤·상큼",
            "5": "진한 감칠맛",
        },
    },
    {
        "key": "main_ingredient",
        "text": "주인공 재료는?",
        "options": {
            "1": "고기",
            "2": "해산물",
            "3": "채소",
            "4": "두부·계란",
            "5": "밥·탄수화물",
        },
    },
    {
        "key": "form",
        "text": "음식 형태는?",
        "options": {
            "1": "밥",
            "2": "면",
            "3": "국물",
            "4": "구이·튀김",
            "5": "분식·간식",
        },
    },
    {
        "key": "spice_level",
        "text": "매운 정도는?",
        "options": {
            "1": "안 매움",
            "2": "약간 매움",
            "3": "매콤",
            "4": "아주 매움",
            "5": "마라·불맛",
        },
    },
    {
        "key": "eating_style",
        "text": "어떻게 먹을 예정이야?",
        "options": {
            "1": "빨리 먹기",
            "2": "앉아서 천천히",
            "3": "나눠먹기",
            "4": "배달·포장",
            "5": "술·야식 같이",
        },
    },
]

QUESTION_WEIGHTS = {
    "situation": 2.4,
    "meal_goal": 3.2,
    "taste_profile": 2.9,
    "main_ingredient": 2.1,
    "form": 2.4,
    "spice_level": 2.1,
    "eating_style": 1.8,
}

ANSWER_KEYS = [question["key"] for question in QUESTIONS]
VALID_OPTION_VALUES_BY_KEY = {
    question["key"]: set(question["options"].values())
    for question in QUESTIONS
}
VALID_FEEDBACK_ACTIONS = {"dislike", "choose", "similar"}

MIN_EXACT_FEEDBACK_COUNT = 3
MIN_PARTIAL_FEEDBACK_COUNT = 6
MIN_PARTIAL_OVERLAP_RATIO = 5 / 7
FEEDBACK_SMOOTHING = 4.0
MAX_EXACT_FEEDBACK_ADJUSTMENT = 1.6
MAX_PARTIAL_FEEDBACK_ADJUSTMENT = 0.5
MAX_SIMILAR_FEEDBACK_ADJUSTMENT = 0.25


# ---------------------------------------------------------
# Food database
# ---------------------------------------------------------
DEFAULT_FOOD_IMAGE_PATH = "/static/foods/default-food.png"

CATEGORY_IMAGE_PATHS = {
    "찌개": "/static/foods/jjigae.png",
    "국밥": "/static/foods/gukbap.png",
    "덮밥": "/static/foods/deopbap.png",
    "마라": "/static/foods/malatang.png",
    "튀김": "/static/foods/donkatsu.png",
    "면": "/static/foods/noodles.png",
    "고기": "/static/foods/meat.png",
    "분식": "/static/foods/bunsik.png",
    "샐러드": "/static/foods/salad.png",
    "밥": "/static/foods/rice.png",
}

FOOD_DB = [
    {
        "name": "김치찌개",
        "category": "찌개",
        "situation": ["혼밥", "친구랑", "가족·동료"],
        "meal_goal": ["속 따뜻한 국물", "든든한 식사", "스트레스 풀 매운맛"],
        "taste_profile": ["매콤", "진한 감칠맛"],
        "main_ingredient": ["밥·탄수화물", "고기", "두부·계란"],
        "form": ["국물", "밥"],
        "spice_level": ["약간 매움", "매콤"],
        "eating_style": ["앉아서 천천히", "배달·포장"],
        "short_desc": "매콤한 국물에 밥까지 든든한 기본기 메뉴",
        "image_path": "/static/foods/generated/kimchi-jjigae-v2.jpg",
    },
    {
        "name": "순두부찌개",
        "category": "찌개",
        "situation": ["혼밥", "가족·동료"],
        "meal_goal": ["속 따뜻한 국물", "든든한 식사"],
        "taste_profile": ["담백", "매콤"],
        "main_ingredient": ["두부·계란", "밥·탄수화물"],
        "form": ["국물", "밥"],
        "spice_level": ["안 매움", "약간 매움", "매콤"],
        "eating_style": ["빨리 먹기", "앉아서 천천히"],
        "short_desc": "부드럽고 따뜻하게 먹기 좋은 국물 메뉴",
        "image_path": "/static/foods/generated/sundubu-jjigae-v2.jpg",
    },
    {
        "name": "제육덮밥",
        "category": "덮밥",
        "situation": ["혼밥", "가족·동료"],
        "meal_goal": ["든든한 식사", "스트레스 풀 매운맛"],
        "taste_profile": ["매콤", "진한 감칠맛"],
        "main_ingredient": ["고기", "밥·탄수화물"],
        "form": ["밥"],
        "spice_level": ["매콤", "아주 매움"],
        "eating_style": ["빨리 먹기", "배달·포장"],
        "short_desc": "매콤한 고기와 밥 조합이 확실한 한 끼",
        "image_path": "/static/foods/generated/jeyuk-deopbap-v2.jpg",
    },
    {
        "name": "마라탕",
        "category": "마라",
        "situation": ["친구랑", "야식"],
        "meal_goal": ["스트레스 풀 매운맛", "새로운 메뉴", "속 따뜻한 국물"],
        "taste_profile": ["매콤", "진한 감칠맛"],
        "main_ingredient": ["채소", "고기", "두부·계란"],
        "form": ["국물"],
        "spice_level": ["아주 매움", "마라·불맛"],
        "eating_style": ["나눠먹기", "배달·포장", "술·야식 같이"],
        "short_desc": "자극적인 국물 메뉴가 당길 때 좋은 선택",
        "image_path": "/static/foods/generated/malatang-v2.jpg",
    },
    {
        "name": "돈까스",
        "category": "튀김",
        "situation": ["혼밥", "친구랑", "가족·동료"],
        "meal_goal": ["든든한 식사"],
        "taste_profile": ["고소·크리미", "진한 감칠맛"],
        "main_ingredient": ["고기"],
        "form": ["구이·튀김"],
        "spice_level": ["안 매움"],
        "eating_style": ["빨리 먹기", "앉아서 천천히"],
        "short_desc": "바삭하고 든든해서 실패 확률이 낮은 메뉴",
        "image_path": "/static/foods/generated/donkatsu-v2.jpg",
    },
    {
        "name": "쌀국수",
        "category": "면",
        "situation": ["혼밥", "데이트", "가족·동료"],
        "meal_goal": ["가볍고 깔끔", "속 따뜻한 국물"],
        "taste_profile": ["담백", "진한 감칠맛"],
        "main_ingredient": ["밥·탄수화물", "채소", "고기"],
        "form": ["면", "국물"],
        "spice_level": ["안 매움", "약간 매움"],
        "eating_style": ["빨리 먹기", "앉아서 천천히"],
        "short_desc": "따뜻하고 깔끔하게 먹기 좋은 면 메뉴",
        "image_path": "/static/foods/generated/pho-v2.jpg",
    },
    {
        "name": "김밥",
        "category": "분식",
        "situation": ["혼밥", "친구랑"],
        "meal_goal": ["가볍고 깔끔"],
        "taste_profile": ["담백", "고소·크리미"],
        "main_ingredient": ["밥·탄수화물", "채소"],
        "form": ["분식·간식", "밥"],
        "spice_level": ["안 매움"],
        "eating_style": ["빨리 먹기", "배달·포장"],
        "short_desc": "가볍고 빠르게 먹기 좋은 부담 없는 한 끼",
        "image_path": "/static/foods/generated/kimbap.jpg",
    },
    {
        "name": "국밥",
        "category": "국밥",
        "situation": ["혼밥", "가족·동료"],
        "meal_goal": ["든든한 식사", "속 따뜻한 국물"],
        "taste_profile": ["담백", "진한 감칠맛"],
        "main_ingredient": ["밥·탄수화물", "고기"],
        "form": ["국물", "밥"],
        "spice_level": ["안 매움", "약간 매움"],
        "eating_style": ["빨리 먹기", "앉아서 천천히"],
        "short_desc": "뜨끈한 국물과 밥으로 든든하게 채우는 메뉴",
        "image_path": "/static/foods/generated/gukbap-v2.jpg",
    },
    {
        "name": "떡볶이",
        "category": "분식",
        "situation": ["친구랑", "야식"],
        "meal_goal": ["스트레스 풀 매운맛", "새로운 메뉴"],
        "taste_profile": ["매콤", "진한 감칠맛"],
        "main_ingredient": ["밥·탄수화물"],
        "form": ["분식·간식"],
        "spice_level": ["매콤", "아주 매움"],
        "eating_style": ["나눠먹기", "배달·포장", "술·야식 같이"],
        "short_desc": "매콤하게 기분 전환하기 좋은 분식 메뉴",
        "image_path": "/static/foods/generated/tteokbokki.jpg",
    },
    {
        "name": "파스타",
        "category": "면",
        "situation": ["데이트", "친구랑"],
        "meal_goal": ["가볍고 깔끔", "새로운 메뉴"],
        "taste_profile": ["고소·크리미", "진한 감칠맛"],
        "main_ingredient": ["밥·탄수화물"],
        "form": ["면"],
        "spice_level": ["안 매움", "약간 매움"],
        "eating_style": ["앉아서 천천히"],
        "short_desc": "분위기 있게 먹기 좋은 부드러운 면 메뉴",
        "image_path": "/static/foods/generated/pasta.jpg",
    },
    {
        "name": "삼겹살",
        "category": "고기",
        "situation": ["친구랑", "가족·동료"],
        "meal_goal": ["든든한 식사"],
        "taste_profile": ["고소·크리미", "진한 감칠맛"],
        "main_ingredient": ["고기"],
        "form": ["구이·튀김"],
        "spice_level": ["안 매움"],
        "eating_style": ["나눠먹기", "술·야식 같이"],
        "short_desc": "여럿이 먹을 때 만족도가 높은 고기 메뉴",
        "image_path": "/static/foods/generated/samgyeopsal.jpg",
    },
    {
        "name": "비빔밥",
        "category": "밥",
        "situation": ["혼밥", "가족·동료"],
        "meal_goal": ["든든한 식사", "가볍고 깔끔"],
        "taste_profile": ["담백", "진한 감칠맛"],
        "main_ingredient": ["밥·탄수화물", "채소"],
        "form": ["밥"],
        "spice_level": ["안 매움", "약간 매움"],
        "eating_style": ["빨리 먹기", "앉아서 천천히"],
        "short_desc": "채소와 밥을 같이 챙기는 균형 잡힌 한 끼",
        "image_path": "/static/foods/generated/bibimbap.jpg",
    },
    {
        "name": "오므라이스",
        "category": "밥",
        "situation": ["혼밥", "데이트", "가족·동료"],
        "meal_goal": ["든든한 식사"],
        "taste_profile": ["고소·크리미", "담백"],
        "main_ingredient": ["두부·계란", "밥·탄수화물"],
        "form": ["밥"],
        "spice_level": ["안 매움"],
        "eating_style": ["빨리 먹기", "앉아서 천천히"],
        "short_desc": "부드럽고 고소해서 자극 없이 든든한 메뉴",
        "image_path": "/static/foods/generated/omurice.jpg",
    },
    {
        "name": "카레라이스",
        "category": "밥",
        "situation": ["혼밥", "가족·동료"],
        "meal_goal": ["든든한 식사"],
        "taste_profile": ["진한 감칠맛", "고소·크리미"],
        "main_ingredient": ["밥·탄수화물", "고기"],
        "form": ["밥"],
        "spice_level": ["약간 매움"],
        "eating_style": ["빨리 먹기", "배달·포장"],
        "short_desc": "빠르고 든든하게 먹기 좋은 밥 메뉴",
        "image_path": "/static/foods/generated/curry-rice.jpg",
    },
    {
        "name": "초밥",
        "category": "밥",
        "situation": ["데이트", "친구랑"],
        "meal_goal": ["가볍고 깔끔", "새로운 메뉴"],
        "taste_profile": ["담백", "새콤·상큼"],
        "main_ingredient": ["해산물", "밥·탄수화물"],
        "form": ["밥"],
        "spice_level": ["안 매움"],
        "eating_style": ["앉아서 천천히", "나눠먹기"],
        "short_desc": "깔끔하고 대화하기 좋은 외식 메뉴",
        "image_path": "/static/foods/generated/sushi.jpg",
    },
    {
        "name": "연어덮밥",
        "category": "덮밥",
        "situation": ["혼밥", "데이트"],
        "meal_goal": ["가볍고 깔끔"],
        "taste_profile": ["담백", "고소·크리미"],
        "main_ingredient": ["해산물", "밥·탄수화물"],
        "form": ["밥"],
        "spice_level": ["안 매움"],
        "eating_style": ["앉아서 천천히"],
        "short_desc": "깔끔하면서도 포만감 있는 덮밥 메뉴",
        "image_path": "/static/foods/generated/salmon-deopbap.jpg",
    },
    {
        "name": "칼국수",
        "category": "면",
        "situation": ["혼밥", "가족·동료"],
        "meal_goal": ["속 따뜻한 국물", "든든한 식사"],
        "taste_profile": ["담백", "진한 감칠맛"],
        "main_ingredient": ["밥·탄수화물"],
        "form": ["면", "국물"],
        "spice_level": ["안 매움"],
        "eating_style": ["앉아서 천천히"],
        "short_desc": "담백한 국물과 면으로 편하게 채우는 메뉴",
        "image_path": "/static/foods/generated/kalguksu.jpg",
    },
    {
        "name": "라멘",
        "category": "면",
        "situation": ["혼밥", "데이트", "야식"],
        "meal_goal": ["속 따뜻한 국물", "든든한 식사", "새로운 메뉴"],
        "taste_profile": ["진한 감칠맛", "고소·크리미", "매콤"],
        "main_ingredient": ["밥·탄수화물", "고기", "두부·계란"],
        "form": ["면", "국물"],
        "spice_level": ["안 매움", "약간 매움", "매콤"],
        "eating_style": ["빨리 먹기", "앉아서 천천히", "술·야식 같이"],
        "short_desc": "진한 국물과 면이 당길 때 좋은 메뉴",
        "image_path": "/static/foods/generated/ramen.jpg",
    },
    {
        "name": "잔치국수",
        "category": "면",
        "situation": ["혼밥", "가족·동료"],
        "meal_goal": ["가볍고 깔끔", "속 따뜻한 국물"],
        "taste_profile": ["담백"],
        "main_ingredient": ["밥·탄수화물"],
        "form": ["면", "국물"],
        "spice_level": ["안 매움"],
        "eating_style": ["빨리 먹기"],
        "short_desc": "가볍고 따뜻해서 부담 없이 먹기 좋은 메뉴",
        "image_path": "/static/foods/generated/janchi-guksu.jpg",
    },
    {
        "name": "냉면",
        "category": "면",
        "situation": ["혼밥", "친구랑"],
        "meal_goal": ["가볍고 깔끔"],
        "taste_profile": ["새콤·상큼", "매콤"],
        "main_ingredient": ["밥·탄수화물"],
        "form": ["면"],
        "spice_level": ["안 매움", "매콤"],
        "eating_style": ["빨리 먹기"],
        "short_desc": "입맛 없을 때 깔끔하게 먹기 좋은 면 메뉴",
        "image_path": "/static/foods/generated/naengmyeon.jpg",
    },
    {
        "name": "부대찌개",
        "category": "찌개",
        "situation": ["친구랑", "가족·동료"],
        "meal_goal": ["든든한 식사", "속 따뜻한 국물", "스트레스 풀 매운맛"],
        "taste_profile": ["매콤", "진한 감칠맛"],
        "main_ingredient": ["고기", "밥·탄수화물"],
        "form": ["국물", "밥"],
        "spice_level": ["매콤"],
        "eating_style": ["나눠먹기", "배달·포장"],
        "short_desc": "매콤한 국물과 밥 조합이 든든한 메뉴",
    },
    {
        "name": "샤브샤브",
        "category": "국물",
        "situation": ["친구랑", "데이트", "가족·동료"],
        "meal_goal": ["가볍고 깔끔", "속 따뜻한 국물"],
        "taste_profile": ["담백", "진한 감칠맛"],
        "main_ingredient": ["고기", "채소"],
        "form": ["국물", "구이·튀김"],
        "spice_level": ["안 매움"],
        "eating_style": ["나눠먹기", "앉아서 천천히"],
        "short_desc": "담백하고 깔끔하게 나눠먹기 좋은 메뉴",
    },
    {
        "name": "찜닭",
        "category": "고기",
        "situation": ["친구랑", "가족·동료"],
        "meal_goal": ["든든한 식사"],
        "taste_profile": ["진한 감칠맛", "매콤"],
        "main_ingredient": ["고기", "밥·탄수화물"],
        "form": ["구이·튀김", "밥"],
        "spice_level": ["약간 매움", "매콤"],
        "eating_style": ["나눠먹기", "배달·포장"],
        "short_desc": "양이 넉넉하고 함께 먹기 좋은 닭요리",
    },
    {
        "name": "치킨",
        "category": "고기",
        "situation": ["친구랑", "야식"],
        "meal_goal": ["든든한 식사", "스트레스 풀 매운맛"],
        "taste_profile": ["고소·크리미", "매콤", "진한 감칠맛"],
        "main_ingredient": ["고기"],
        "form": ["구이·튀김"],
        "spice_level": ["안 매움", "매콤"],
        "eating_style": ["나눠먹기", "배달·포장", "술·야식 같이"],
        "short_desc": "야식이나 친구랑 먹기 좋은 대표 메뉴",
    },
    {
        "name": "보쌈",
        "category": "고기",
        "situation": ["친구랑", "가족·동료", "데이트"],
        "meal_goal": ["든든한 식사"],
        "taste_profile": ["담백", "고소·크리미"],
        "main_ingredient": ["고기"],
        "form": ["구이·튀김"],
        "spice_level": ["안 매움"],
        "eating_style": ["나눠먹기", "앉아서 천천히"],
        "short_desc": "자극이 덜하고 든든하게 나눠먹기 좋은 메뉴",
    },
    {
        "name": "닭갈비",
        "category": "고기",
        "situation": ["친구랑", "가족·동료"],
        "meal_goal": ["든든한 식사", "스트레스 풀 매운맛"],
        "taste_profile": ["매콤", "진한 감칠맛"],
        "main_ingredient": ["고기", "밥·탄수화물"],
        "form": ["구이·튀김", "밥"],
        "spice_level": ["매콤", "아주 매움"],
        "eating_style": ["나눠먹기", "앉아서 천천히"],
        "short_desc": "매콤하고 볶음밥까지 이어가기 좋은 메뉴",
    },
    {
        "name": "햄버거",
        "category": "고기",
        "situation": ["혼밥", "야식"],
        "meal_goal": ["든든한 식사"],
        "taste_profile": ["고소·크리미", "진한 감칠맛"],
        "main_ingredient": ["고기", "밥·탄수화물"],
        "form": ["구이·튀김", "분식·간식"],
        "spice_level": ["안 매움", "약간 매움"],
        "eating_style": ["빨리 먹기", "배달·포장"],
        "short_desc": "빠르게 먹기 좋고 든든한 한 끼",
    },
    {
        "name": "포케",
        "category": "밥",
        "situation": ["혼밥", "데이트"],
        "meal_goal": ["가볍고 깔끔"],
        "taste_profile": ["담백", "새콤·상큼"],
        "main_ingredient": ["채소", "해산물", "밥·탄수화물"],
        "form": ["밥"],
        "spice_level": ["안 매움"],
        "eating_style": ["빨리 먹기", "앉아서 천천히"],
        "short_desc": "깔끔하지만 허전하지 않은 균형 잡힌 메뉴",
    },
    {
        "name": "토스트",
        "category": "분식",
        "situation": ["혼밥"],
        "meal_goal": ["가볍고 깔끔"],
        "taste_profile": ["고소·크리미", "담백"],
        "main_ingredient": ["밥·탄수화물", "두부·계란"],
        "form": ["분식·간식"],
        "spice_level": ["안 매움"],
        "eating_style": ["빨리 먹기", "배달·포장"],
        "short_desc": "간단하고 빠르게 허기를 채우기 좋은 메뉴",
    },
    {
        "name": "죽",
        "category": "밥",
        "situation": ["혼밥", "가족·동료"],
        "meal_goal": ["가볍고 깔끔", "속 따뜻한 국물"],
        "taste_profile": ["담백"],
        "main_ingredient": ["밥·탄수화물"],
        "form": ["밥"],
        "spice_level": ["안 매움"],
        "eating_style": ["빨리 먹기", "앉아서 천천히"],
        "short_desc": "속이 편하고 부담 없는 따뜻한 메뉴",
    },
    {
        "name": "우동",
        "category": "면",
        "situation": ["혼밥", "야식"],
        "meal_goal": ["가볍고 깔끔", "속 따뜻한 국물"],
        "taste_profile": ["담백", "진한 감칠맛"],
        "main_ingredient": ["밥·탄수화물"],
        "form": ["면", "국물"],
        "spice_level": ["안 매움"],
        "eating_style": ["빨리 먹기", "술·야식 같이"],
        "short_desc": "따뜻하고 간단해서 늦은 시간에도 부담 적은 메뉴",
    },
    {
        "name": "짬뽕",
        "category": "면",
        "situation": ["혼밥", "친구랑", "야식"],
        "meal_goal": ["스트레스 풀 매운맛", "속 따뜻한 국물", "든든한 식사"],
        "taste_profile": ["매콤", "진한 감칠맛"],
        "main_ingredient": ["해산물", "밥·탄수화물"],
        "form": ["면", "국물"],
        "spice_level": ["매콤", "아주 매움"],
        "eating_style": ["빨리 먹기", "술·야식 같이"],
        "short_desc": "얼큰한 국물과 면으로 매운 욕구를 채우는 메뉴",
    },
    {
        "name": "짜장면",
        "category": "면",
        "situation": ["혼밥", "친구랑", "가족·동료"],
        "meal_goal": ["든든한 식사"],
        "taste_profile": ["진한 감칠맛", "고소·크리미"],
        "main_ingredient": ["밥·탄수화물"],
        "form": ["면"],
        "spice_level": ["안 매움"],
        "eating_style": ["빨리 먹기", "배달·포장"],
        "short_desc": "빠르고 든든하게 먹기 좋은 중식 메뉴",
    },
    {
        "name": "타코",
        "category": "고기",
        "situation": ["친구랑", "데이트"],
        "meal_goal": ["새로운 메뉴", "가볍고 깔끔"],
        "taste_profile": ["매콤", "새콤·상큼"],
        "main_ingredient": ["고기", "채소"],
        "form": ["분식·간식", "구이·튀김"],
        "spice_level": ["약간 매움", "매콤"],
        "eating_style": ["나눠먹기", "앉아서 천천히"],
        "short_desc": "가볍고 색다른 느낌을 주기 좋은 메뉴",
    },
    {
        "name": "분짜",
        "category": "면",
        "situation": ["데이트", "친구랑"],
        "meal_goal": ["가볍고 깔끔", "새로운 메뉴"],
        "taste_profile": ["새콤·상큼", "담백"],
        "main_ingredient": ["고기", "채소", "밥·탄수화물"],
        "form": ["면"],
        "spice_level": ["안 매움"],
        "eating_style": ["앉아서 천천히"],
        "short_desc": "상큼하고 깔끔해서 무겁지 않은 외식 메뉴",
    },
]


# ---------------------------------------------------------
# Food metadata helpers
# ---------------------------------------------------------
def make_public_url(path_or_url: Optional[str]) -> str:
    if not path_or_url:
        path_or_url = DEFAULT_FOOD_IMAGE_PATH

    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url

    if FOOD_IMAGE_BASE_URL and path_or_url.startswith("/static/foods/generated/"):
        return f"{FOOD_IMAGE_BASE_URL}/{os.path.basename(path_or_url)}"

    if not path_or_url.startswith("/"):
        path_or_url = f"/{path_or_url}"

    return f"{PUBLIC_BASE_URL}{path_or_url}"


def collect_food_tags(food: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    for key in ANSWER_KEYS:
        value = food.get(key, [])
        if isinstance(value, list):
            tags.extend(value)
        elif value:
            tags.append(str(value))

    category = food.get("category")
    if category:
        tags.append(str(category))

    return list(dict.fromkeys(tags))


def setup_food_card_fields() -> None:
    for food in FOOD_DB:
        image_path = food.get("image_path") or CATEGORY_IMAGE_PATHS.get(food.get("category"), DEFAULT_FOOD_IMAGE_PATH)
        food["image_url"] = make_public_url(image_path)
        food["tags"] = collect_food_tags(food)


setup_food_card_fields()


# ---------------------------------------------------------
# Kakao response builders
# ---------------------------------------------------------
def make_quick_replies(labels: List[str]) -> List[Dict[str, str]]:
    return [
        {
            "action": "message",
            "label": label,
            "messageText": label,
        }
        for label in labels
    ]


def kakao_text_response(text: str, quick_replies: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    template: Dict[str, Any] = {
        "outputs": [
            {
                "simpleText": {
                    "text": text,
                }
            }
        ]
    }

    if quick_replies:
        template["quickReplies"] = quick_replies

    return {
        "version": "2.0",
        "template": template,
    }


def build_start_response() -> Dict[str, Any]:
    return kakao_text_response(
        text="오늘 뭐 먹을지 정해볼게. 아래 버튼으로 시작해줘.",
        quick_replies=make_quick_replies(["오늘 뭐 먹지"]),
    )


def build_question_response(step: int) -> Dict[str, Any]:
    question = QUESTIONS[step]
    options = list(question["options"].values())

    return kakao_text_response(
        text=f"{step + 1}. {question['text']}",
        quick_replies=make_quick_replies(options),
    )


def build_recommendation_response(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    cards = []

    for item in recommendations[:3]:
        card: Dict[str, Any] = {
            "title": item["name"],
            "description": item.get("short_desc", "지금 먹기 좋은 메뉴야."),
            "buttons": [
                {
                    "action": "message",
                    "label": "이걸로 결정",
                    "messageText": f"{item['name']} 선택",
                },
                {
                    "action": "message",
                    "label": "비슷한 메뉴 더 보기",
                    "messageText": f"{item['name']} 비슷한 메뉴",
                },
                {
                    "action": "message",
                    "label": "별로예요",
                    "messageText": f"{item['name']} 별로예요",
                },
            ],
        }

        image_url = item.get("image_url")
        if image_url:
            card["thumbnail"] = {"imageUrl": image_url}

        cards.append(card)

    if not cards:
        return kakao_text_response(
            text="추천할 메뉴를 찾지 못했어. 다시 골라보자.",
            quick_replies=make_quick_replies(["다시 추천"]),
        )

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": cards,
                    }
                }
            ],
            "quickReplies": make_quick_replies(["다시 추천"]),
        },
    }


# ---------------------------------------------------------
# Session persistence
# ---------------------------------------------------------
def get_session(user_id: str) -> Optional[Dict[str, Any]]:
    if supabase is None:
        return USER_SESSIONS.get(user_id)

    try:
        result = (
            supabase.table("user_sessions")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        print(f"WARNING: Failed to fetch session from Supabase: {exc}")
        return USER_SESSIONS.get(user_id)

    if not result.data:
        return None

    row = result.data[0]
    return {
        "step": row.get("step", 0),
        "answers": row.get("answers", {}),
        "recommendations": row.get("recommendations", []),
    }


def save_session(user_id: str, session: Dict[str, Any]) -> None:
    USER_SESSIONS[user_id] = session

    if supabase is None:
        return

    payload = {
        "user_id": user_id,
        "step": session.get("step", 0),
        "answers": session.get("answers", {}),
        "recommendations": session.get("recommendations", []),
    }

    try:
        supabase.table("user_sessions").upsert(payload).execute()
    except Exception as exc:
        print(f"WARNING: Failed to save session to Supabase: {exc}")


def reset_session(user_id: str) -> Dict[str, Any]:
    session = {
        "step": 0,
        "answers": {},
        "recommendations": [],
    }
    save_session(user_id, session)
    return session


# ---------------------------------------------------------
# Feedback persistence and online learning
# ---------------------------------------------------------
def answer_signature(answers: Dict[str, Any]) -> str:
    parts = []
    for key in ANSWER_KEYS:
        value = answers.get(key)
        if value:
            parts.append(f"{key}={value}")
    return "|".join(parts)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def is_valid_answer_payload(answers: Any) -> bool:
    if not isinstance(answers, dict) or not answers:
        return False

    for key, value in answers.items():
        if key not in VALID_OPTION_VALUES_BY_KEY:
            return False
        if value not in VALID_OPTION_VALUES_BY_KEY[key]:
            return False

    return True


def is_valid_feedback_record(record: Dict[str, Any]) -> bool:
    menu_name = record.get("menu_name")
    action = record.get("action")
    answers = record.get("answers")
    known_menu_names = {food["name"] for food in FOOD_DB}

    if menu_name not in known_menu_names:
        return False
    if action not in VALID_FEEDBACK_ACTIONS:
        return False
    if not is_valid_answer_payload(answers):
        return False

    return True


def score_learned_weight_adjustment(food: Dict[str, Any], answers: Dict[str, Any]) -> float:
    if not LEARNED_MENU_WEIGHTS:
        return 0.0

    menu_name = food.get("name")
    signature = answer_signature(answers)
    score = 0.0

    global_weights = LEARNED_MENU_WEIGHTS.get("global", {})
    signature_weights = LEARNED_MENU_WEIGHTS.get("by_signature", {})

    try:
        score += float(global_weights.get(menu_name, 0.0))
        score += float(signature_weights.get(signature, {}).get(menu_name, 0.0))
    except (TypeError, ValueError):
        return 0.0

    return score


def get_feedback_records() -> List[Dict[str, Any]]:
    if supabase is None:
        return MENU_FEEDBACK

    try:
        result = (
            supabase.table("menu_feedback")
            .select("user_id, menu_name, action, answers, answer_signature")
            .limit(2000)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        print(f"WARNING: Failed to fetch menu feedback from Supabase: {exc}")
        return MENU_FEEDBACK


def save_feedback(user_id: str, menu_name: str, action: str, answers: Dict[str, Any]) -> None:
    if not menu_name:
        return

    if action not in VALID_FEEDBACK_ACTIONS:
        return

    payload = {
        "user_id": user_id,
        "menu_name": menu_name,
        "action": action,
        "answers": answers,
        "answer_signature": answer_signature(answers),
    }

    MENU_FEEDBACK.append(payload)

    if supabase is None:
        return

    try:
        supabase.table("menu_feedback").insert(payload).execute()
    except Exception as exc:
        print(f"WARNING: Failed to save menu feedback to Supabase: {exc}")


def get_toss_usage_events() -> List[Dict[str, Any]]:
    if supabase is None:
        return TOSS_USAGE_EVENTS

    try:
        result = (
            supabase.table("toss_usage_events")
            .select("user_id, event_name, metadata")
            .limit(5000)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        print(f"WARNING: Failed to fetch Toss usage events from Supabase: {exc}")
        return TOSS_USAGE_EVENTS


def save_toss_usage_event(user_id: str, event_name: str, metadata: Dict[str, Any]) -> None:
    payload = {
        "user_id": user_id,
        "event_name": event_name,
        "metadata": metadata,
    }

    TOSS_USAGE_EVENTS.append(payload)

    if supabase is None:
        return

    try:
        supabase.table("toss_usage_events").insert(payload).execute()
    except Exception as exc:
        print(f"WARNING: Failed to save Toss usage event to Supabase: {exc}")


def summarize_toss_usage_events(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    event_counts = {event_name: 0 for event_name in sorted(TOSS_USAGE_EVENT_NAMES)}
    unique_user_ids = set()

    for record in records:
        event_name = record.get("event_name") or record.get("event")
        if event_name in event_counts:
            event_counts[event_name] += 1

        user_id = normalize_toss_user_id(record.get("user_id") or record.get("userId"))
        unique_user_ids.add(user_id)

    return {
        "uniqueUsers": len(unique_user_ids),
        "eventsTotal": sum(event_counts.values()),
        "events": event_counts,
    }


def answers_overlap_ratio(current_answers: Dict[str, Any], past_answers: Dict[str, Any]) -> float:
    compared = 0
    matched = 0

    for key in ANSWER_KEYS:
        current_value = current_answers.get(key)
        if not current_value:
            continue

        compared += 1
        if past_answers.get(key) == current_value:
            matched += 1

    if compared == 0:
        return 0.0

    return matched / compared


def score_feedback_adjustment(
    food: Dict[str, Any],
    answers: Dict[str, Any],
    feedback_records: List[Dict[str, Any]],
) -> float:
    if not is_valid_answer_payload(answers):
        return 0.0

    current_signature = answer_signature(answers)
    exact_counts = {"dislike": 0.0, "choose": 0.0, "similar": 0.0}
    partial_counts = {"dislike": 0.0, "choose": 0.0, "similar": 0.0}
    seen_feedback_keys = set()

    for index, record in enumerate(feedback_records):
        if not is_valid_feedback_record(record):
            continue

        if record.get("menu_name") != food.get("name"):
            continue

        action = record.get("action")
        record_answers = record.get("answers") or {}
        record_signature = record.get("answer_signature") or answer_signature(record_answers)
        user_id = record.get("user_id") or f"anonymous-{index}"
        dedupe_key = (user_id, action, record_signature)

        if dedupe_key in seen_feedback_keys:
            continue

        seen_feedback_keys.add(dedupe_key)

        if record_signature == current_signature and current_signature:
            exact_counts[action] += 1.0
            continue

        overlap = answers_overlap_ratio(answers, record_answers)
        if overlap < MIN_PARTIAL_OVERLAP_RATIO:
            continue

        partial_counts[action] += overlap

    exact_total = exact_counts["dislike"] + exact_counts["choose"]
    exact_score = 0.0
    if exact_total >= MIN_EXACT_FEEDBACK_COUNT:
        exact_net = exact_counts["choose"] - exact_counts["dislike"]
        exact_score = clamp(
            (exact_net / (exact_total + FEEDBACK_SMOOTHING)) * MAX_EXACT_FEEDBACK_ADJUSTMENT,
            -MAX_EXACT_FEEDBACK_ADJUSTMENT,
            MAX_EXACT_FEEDBACK_ADJUSTMENT,
        )

    partial_total = partial_counts["dislike"] + partial_counts["choose"]
    partial_score = 0.0
    if partial_total >= MIN_PARTIAL_FEEDBACK_COUNT:
        partial_net = partial_counts["choose"] - partial_counts["dislike"]
        partial_score = clamp(
            (partial_net / (partial_total + FEEDBACK_SMOOTHING)) * MAX_PARTIAL_FEEDBACK_ADJUSTMENT,
            -MAX_PARTIAL_FEEDBACK_ADJUSTMENT,
            MAX_PARTIAL_FEEDBACK_ADJUSTMENT,
        )

    similar_count = exact_counts["similar"] + partial_counts["similar"]
    similar_score = 0.0
    if similar_count >= MIN_EXACT_FEEDBACK_COUNT:
        similar_score = min(MAX_SIMILAR_FEEDBACK_ADJUSTMENT, similar_count * 0.03)

    return exact_score + partial_score + similar_score


# ---------------------------------------------------------
# Recommendation scoring
# ---------------------------------------------------------
def score_food_attribute_matches(food: Dict[str, Any], answers: Dict[str, Any]) -> float:
    score = 0.0

    for key, selected_value in answers.items():
        if key not in ANSWER_KEYS:
            continue

        food_values = food.get(key, [])
        if not isinstance(food_values, list):
            food_values = [food_values]

        if selected_value in food_values:
            score += QUESTION_WEIGHTS.get(key, 1.0)

    return score


def score_combo_adjustments(food: Dict[str, Any], answers: Dict[str, Any]) -> float:
    score = 0.0
    category = food.get("category")
    tags = set(food.get("tags", []))

    situation = answers.get("situation")
    meal_goal = answers.get("meal_goal")
    taste_profile = answers.get("taste_profile")
    form = answers.get("form")
    spice_level = answers.get("spice_level")
    eating_style = answers.get("eating_style")

    if meal_goal == "스트레스 풀 매운맛":
        if "매콤" in tags or "아주 매움" in tags or "마라·불맛" in tags:
            score += 1.8
        if category == "마라":
            score += 1.5

    if meal_goal == "속 따뜻한 국물" and "국물" in tags:
        score += 2.0

    if meal_goal == "가볍고 깔끔":
        if category in {"샐러드", "면"} or "담백" in tags or "새콤·상큼" in tags:
            score += 1.4
        if category in {"튀김", "마라"}:
            score -= 0.8

    if meal_goal == "새로운 메뉴":
        if category in {"마라", "고기", "면", "샐러드"}:
            score += 1.0

    if situation == "혼밥" and eating_style == "빨리 먹기":
        if category in {"덮밥", "면", "국밥", "분식", "밥"}:
            score += 1.2

    if situation == "데이트":
        if category in {"면", "고기", "샐러드"}:
            score += 1.0
        if category in {"찌개", "국밥"} and eating_style != "앉아서 천천히":
            score -= 0.6

    if situation == "야식" or eating_style == "술·야식 같이":
        if category in {"마라", "분식", "튀김", "고기", "면"}:
            score += 1.3

    if taste_profile == "고소·크리미" and category in {"튀김", "면", "밥"}:
        score += 0.8

    if taste_profile == "새콤·상큼" and category in {"샐러드", "면", "고기"}:
        score += 1.0

    if form == "국물" and category in {"찌개", "국밥", "마라", "면"}:
        score += 0.9

    if spice_level == "안 매움" and ("아주 매움" in tags or "마라·불맛" in tags):
        score -= 3.0

    if spice_level in {"아주 매움", "마라·불맛"} and category in {"마라", "면", "분식"}:
        score += 1.4

    return score


def food_to_recommendation(food: Dict[str, Any], score: float = 0.0) -> Dict[str, Any]:
    return {
        "name": food["name"],
        "score": round(score, 3),
        "short_desc": food.get("short_desc", "지금 먹기 좋은 메뉴야."),
        "image_url": food.get("image_url"),
        "category": food.get("category"),
        "tags": food.get("tags", []),
    }


def recommend_food(answers: Dict[str, Any], exclude_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    exclude_set = set(exclude_names or [])
    feedback_records = get_feedback_records()
    scored_foods = []

    for food in FOOD_DB:
        if food["name"] in exclude_set:
            continue

        score = score_food_attribute_matches(food, answers)
        score += score_combo_adjustments(food, answers)
        score += score_feedback_adjustment(food, answers, feedback_records)
        score += score_learned_weight_adjustment(food, answers)
        scored_foods.append((score, food))

    scored_foods.sort(key=lambda item: (-item[0], item[1]["name"]))
    return [food_to_recommendation(food, score) for score, food in scored_foods[:3]]


def recommend_similar_food(menu_name: str) -> List[Dict[str, Any]]:
    target_food = next((food for food in FOOD_DB if food["name"] == menu_name), None)

    if target_food is None:
        return [food_to_recommendation(food, 0.0) for food in FOOD_DB[:3]]

    target_tags = set(target_food.get("tags", []))
    target_category = target_food.get("category")
    similar_foods = []

    for food in FOOD_DB:
        if food["name"] == menu_name:
            continue

        overlap_count = len(target_tags.intersection(food.get("tags", [])))
        same_category_bonus = 10 if food.get("category") == target_category else 0
        score = same_category_bonus + overlap_count
        similar_foods.append((score, food))

    similar_foods.sort(key=lambda item: (-item[0], item[1]["name"]))
    return [food_to_recommendation(food, score) for score, food in similar_foods[:3]]


# ---------------------------------------------------------
# Conversation handling
# ---------------------------------------------------------
def normalize_utterance(utterance: str) -> str:
    drop_chars = set(" \t\r\n.!?,。！？·")
    return "".join(ch for ch in utterance.strip().lower() if ch not in drop_chars)


def is_start_message(normalized: str) -> bool:
    start_keywords = {
        "오늘뭐먹지",
        "뭐먹지",
        "뭐먹을까",
        "메뉴추천",
        "음식추천",
        "시작",
        "추천",
    }
    return normalized in start_keywords


def is_reset_message(normalized: str) -> bool:
    reset_keywords = {
        "다시추천",
        "처음부터",
        "재시작",
        "다시",
        "초기화",
    }
    return normalized in reset_keywords


def parse_answer(normalized: str, options: Dict[str, str]) -> Optional[str]:
    if normalized in options:
        return options[normalized]

    for value in options.values():
        if normalized == normalize_utterance(value):
            return value

    return None


def public_question_payload() -> List[Dict[str, Any]]:
    return [
        {
            "key": question["key"],
            "text": question["text"],
            "options": [
                {
                    "value": value,
                    "label": value,
                }
                for value in question["options"].values()
            ],
        }
        for question in QUESTIONS
    ]


def validate_toss_answers(answers: Dict[str, Any]) -> Dict[str, str]:
    if not isinstance(answers, dict):
        raise ValueError("Answers must be an object.")

    validated: Dict[str, str] = {}

    for key in ANSWER_KEYS:
        if key not in answers:
            raise ValueError(f"Missing answer: {key}")

        value = str(answers[key]).strip()
        if value not in VALID_OPTION_VALUES_BY_KEY[key]:
            raise ValueError(f"Invalid answer for {key}: {value}")

        validated[key] = value

    return validated


def toss_recommendation_payload(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "name": item["name"],
            "score": item.get("score", 0),
            "shortDesc": item.get("short_desc", "지금 먹기 좋은 메뉴야."),
            "imageUrl": item.get("image_url"),
            "category": item.get("category"),
            "tags": item.get("tags", []),
        }
        for item in recommendations
    ]


def normalize_toss_user_id(value: Any) -> str:
    user_id = str(value or "").strip()
    return user_id or "anonymous"


def strip_action_suffix(utterance: str, suffixes: List[str]) -> str:
    text = utterance.strip()

    for suffix in suffixes:
        if text.endswith(suffix):
            return text[: -len(suffix)].strip()

    normalized_text = normalize_utterance(text)
    for food in FOOD_DB:
        normalized_name = normalize_utterance(food["name"])
        if normalized_text.startswith(normalized_name):
            return food["name"]

    return text


def handle_pickly_flow(user_id: str, utterance: str) -> Dict[str, Any]:
    normalized = normalize_utterance(utterance)
    session = get_session(user_id)
    answers = session.get("answers", {}) if session else {}

    if normalized.endswith("선택"):
        menu_name = strip_action_suffix(utterance, ["선택"])
        save_feedback(user_id, menu_name, "choose", answers)
        return kakao_text_response(
            text=f"{menu_name} 좋다. 이걸로 가자.",
            quick_replies=make_quick_replies(["다시 추천"]),
        )

    if normalized.endswith("비슷한메뉴"):
        menu_name = strip_action_suffix(utterance, ["비슷한 메뉴", "비슷한메뉴"])
        save_feedback(user_id, menu_name, "similar", answers)
        return build_recommendation_response(recommend_similar_food(menu_name))

    if normalized.endswith("별로예요") or normalized.endswith("별로"):
        menu_name = strip_action_suffix(utterance, ["별로예요", "별로"])
        save_feedback(user_id, menu_name, "dislike", answers)

        if answers:
            recommendations = recommend_food(answers, exclude_names=[menu_name])
        else:
            recommendations = recommend_similar_food(menu_name)

        if session is not None:
            session["recommendations"] = recommendations
            save_session(user_id, session)

        return build_recommendation_response(recommendations)

    if is_reset_message(normalized):
        reset_session(user_id)
        return build_question_response(0)

    if is_start_message(normalized):
        reset_session(user_id)
        return build_question_response(0)

    if session is None:
        return build_start_response()

    step = session.get("step", 0)

    if step >= len(QUESTIONS):
        return kakao_text_response(
            text="이미 추천이 끝났어. 다시 추천받고 싶으면 아래 버튼을 눌러줘.",
            quick_replies=make_quick_replies(["다시 추천"]),
        )

    current_question = QUESTIONS[step]
    selected_value = parse_answer(normalized, current_question["options"])

    if selected_value is None:
        return build_question_response(step)

    answer_key = current_question["key"]
    session["answers"][answer_key] = selected_value
    session["step"] = step + 1

    if session["step"] < len(QUESTIONS):
        save_session(user_id, session)
        return build_question_response(session["step"])

    recommendations = recommend_food(session["answers"])
    session["recommendations"] = recommendations
    save_session(user_id, session)

    return build_recommendation_response(recommendations)


def get_kakao_user_id(payload: Dict[str, Any]) -> str:
    user_request = payload.get("userRequest", {})
    user = user_request.get("user", {}) or {}
    properties = user.get("properties", {}) or {}

    return (
        user.get("id")
        or properties.get("plusfriendUserKey")
        or payload.get("bot", {}).get("id")
        or "anonymous"
    )


def get_kakao_utterance(payload: Dict[str, Any]) -> str:
    return str(payload.get("userRequest", {}).get("utterance", "")).strip()


# ---------------------------------------------------------
# API routes
# ---------------------------------------------------------
@app.get("/")
def health_check() -> Dict[str, str]:
    return {
        "status": "ok",
        "message": "PICKY Kakao bot server is running",
    }


@app.get("/api/toss/health")
def toss_health_check() -> Dict[str, str]:
    return {
        "status": "ok",
    }


@app.get("/api/toss/questions")
def toss_questions() -> Dict[str, Any]:
    questions = public_question_payload()
    return {
        "total": len(questions),
        "questions": questions,
    }


@app.post("/api/toss/recommend")
async def toss_recommend(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    try:
        answers = validate_toss_answers(payload.get("answers", {}))
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    user_id = normalize_toss_user_id(payload.get("userId"))
    exclude_names = payload.get("excludeNames", [])
    if not isinstance(exclude_names, list):
        exclude_names = []

    recommendations = recommend_food(
        answers,
        exclude_names=[str(name) for name in exclude_names],
    )

    save_session(
        user_id,
        {
            "step": len(QUESTIONS),
            "answers": answers,
            "recommendations": recommendations,
        },
    )

    return JSONResponse(
        content={
            "userId": user_id,
            "recommendations": toss_recommendation_payload(recommendations),
        }
    )


@app.post("/api/toss/feedback")
async def toss_feedback(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    try:
        answers = validate_toss_answers(payload.get("answers", {}))
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    user_id = normalize_toss_user_id(payload.get("userId"))
    menu_name = str(payload.get("menuName", "")).strip()
    action = str(payload.get("action", "")).strip()

    if action not in VALID_FEEDBACK_ACTIONS:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid feedback action: {action}"},
        )

    if not menu_name:
        return JSONResponse(status_code=400, content={"detail": "Missing menuName"})

    save_feedback(user_id, menu_name, action, answers)

    response: Dict[str, Any] = {
        "status": "ok",
        "userId": user_id,
        "action": action,
        "menuName": menu_name,
    }

    if action == "similar":
        response["recommendations"] = toss_recommendation_payload(recommend_similar_food(menu_name))

    if action == "dislike":
        response["recommendations"] = toss_recommendation_payload(
            recommend_food(answers, exclude_names=[menu_name])
        )

    return JSONResponse(content=response)


@app.post("/api/toss/events")
async def toss_usage_event(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    user_id = normalize_toss_user_id(payload.get("userId"))
    event_name = str(payload.get("event", "")).strip()
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    if event_name not in TOSS_USAGE_EVENT_NAMES:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid event: {event_name}"},
        )

    save_toss_usage_event(user_id, event_name, metadata)

    return JSONResponse(
        content={
            "status": "ok",
            "userId": user_id,
            "event": event_name,
        }
    )


@app.get("/api/toss/metrics")
def toss_usage_metrics() -> Dict[str, Any]:
    return summarize_toss_usage_events(get_toss_usage_events())


@app.post("/kakao/skill")
async def kakao_skill(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    user_id = get_kakao_user_id(payload)
    utterance = get_kakao_utterance(payload)

    response = handle_pickly_flow(user_id=user_id, utterance=utterance)
    return JSONResponse(content=response)
