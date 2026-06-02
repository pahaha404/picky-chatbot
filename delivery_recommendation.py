from __future__ import annotations

from collections import Counter
from math import log2
from typing import Any, Dict, Iterable, List, Optional, Set


DELIVERY_QUESTIONS: List[Dict[str, Any]] = [
    {
        "key": "craving",
        "text": "오늘 당기는 건?",
        "options": ["밥", "면", "국물", "고기", "분식", "치킨피자", "디저트"],
    },
    {
        "key": "cuisine",
        "text": "음식 계열은?",
        "options": ["한식", "중식", "일식", "양식", "기타"],
    },
    {
        "key": "spice",
        "text": "매운 정도는?",
        "options": ["안매움", "매콤", "얼큰", "매움", "마라"],
    },
    {
        "key": "soup",
        "text": "국물은?",
        "options": ["없음", "찌개", "탕국밥", "면국물", "상관없음"],
    },
    {
        "key": "flavor",
        "text": "맛 방향은?",
        "options": ["매콤한", "짭짤한", "고소한", "새콤한", "담백한", "달콤한"],
    },
    {
        "key": "main",
        "text": "메인 재료는?",
        "options": ["돼지", "소", "닭", "해산물", "두부계란", "채소", "상관없음"],
    },
    {
        "key": "meat_type",
        "text": "고기라면?",
        "options": ["돼지", "소", "닭", "족발보쌈", "고기말고", "상관없음"],
        "condition": {"craving": "고기"},
    },
    {
        "key": "rice_style",
        "text": "밥 메뉴라면?",
        "options": ["덮밥", "비빔밥", "김밥", "죽", "백반", "상관없음"],
        "condition": {"craving": "밥"},
    },
    {
        "key": "noodle_style",
        "text": "면이라면?",
        "options": ["짜장", "짬뽕", "라멘우동", "국수냉면", "파스타", "아시안면", "상관없음"],
        "condition": {"craving": "면"},
    },
    {
        "key": "soup_style",
        "text": "국물 종류는?",
        "options": ["찌개", "해장국", "전골탕", "해물탕", "맑은국물", "상관없음"],
        "condition": {"craving": "국물"},
    },
    {
        "key": "snack_style",
        "text": "분식이라면?",
        "options": ["떡볶이", "김밥", "튀김만두", "순대", "토스트핫도그", "상관없음"],
        "condition": {"craving": "분식"},
    },
    {
        "key": "party_food",
        "text": "치킨피자라면?",
        "options": ["후라이드", "양념", "피자", "버거", "족발보쌈", "상관없음"],
        "condition": {"craving": "치킨피자"},
    },
    {
        "key": "dessert_type",
        "text": "디저트라면?",
        "options": ["커피", "빵케이크", "빙수", "아이스크림", "과일", "상관없음"],
        "condition": {"craving": "디저트"},
    },
    {
        "key": "cook",
        "text": "조리 방법은?",
        "options": ["구이", "튀김", "볶음", "찜조림", "차가운", "생"],
    },
    {
        "key": "situation",
        "text": "누구랑 먹어?",
        "options": ["혼자", "둘이", "여럿", "술안주", "가족", "야식"],
    },
    {
        "key": "avoid",
        "text": "먹기 싫은 건?",
        "options": ["매운거", "기름진거", "밀가루", "해산물", "없음"],
    },
]

QUESTION_BY_KEY = {question["key"]: question for question in DELIVERY_QUESTIONS}
QUESTION_KEYS = [question["key"] for question in DELIVERY_QUESTIONS]

QUESTION_WEIGHTS = {
    "craving": 7.0,
    "cuisine": 5.5,
    "spice": 4.7,
    "soup": 4.2,
    "flavor": 4.4,
    "main": 4.0,
    "meat_type": 5.0,
    "rice_style": 5.0,
    "noodle_style": 5.0,
    "soup_style": 5.0,
    "snack_style": 5.0,
    "party_food": 5.0,
    "dessert_type": 5.0,
    "cook": 3.5,
    "situation": 3.0,
}

SPECIALIZED_BY_CRAVING = {
    "밥": "rice_style",
    "면": "noodle_style",
    "국물": "soup_style",
    "고기": "meat_type",
    "분식": "snack_style",
    "치킨피자": "party_food",
    "디저트": "dessert_type",
}
EARLY_PRIORITY_KEYS = ("cuisine", "spice")


def menu(
    name: str,
    delivery_category: str,
    profile: Dict[str, str],
    short_desc: str,
    tags: Optional[Iterable[str]] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    menu_tags = list(dict.fromkeys([delivery_category, *profile.values(), *(tags or [])]))
    return {
        "name": name,
        "delivery_category": delivery_category,
        "category": category or delivery_category,
        "profile": profile,
        "short_desc": short_desc,
        "tags": menu_tags,
    }


DELIVERY_MENUS: List[Dict[str, Any]] = [
    menu("후라이드치킨", "치킨", {"craving": "치킨피자", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "닭", "party_food": "후라이드", "cook": "튀김", "situation": "야식"}, "바삭한 치킨이 당길 때 가장 안전한 선택"),
    menu("양념치킨", "치킨", {"craving": "치킨피자", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "매콤한", "main": "닭", "party_food": "양념", "cook": "튀김", "situation": "야식"}, "달짝매콤한 양념으로 야식 만족도가 높은 메뉴"),
    menu("간장치킨", "치킨", {"craving": "치킨피자", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "짭짤한", "main": "닭", "party_food": "양념", "cook": "튀김", "situation": "여럿"}, "짭짤하고 부담 적은 치킨"),
    menu("매운치킨", "치킨", {"craving": "치킨피자", "cuisine": "한식", "spice": "매움", "soup": "없음", "flavor": "매콤한", "main": "닭", "party_food": "양념", "cook": "튀김", "situation": "야식"}, "매운맛으로 스트레스를 풀기 좋은 치킨"),
    menu("닭강정", "치킨", {"craving": "분식", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "달콤한", "main": "닭", "snack_style": "튀김만두", "cook": "튀김", "situation": "여럿"}, "한입씩 나눠먹기 좋은 달콤매콤한 닭튀김"),
    menu("치킨텐더", "치킨", {"craving": "치킨피자", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "담백한", "main": "닭", "party_food": "후라이드", "cook": "튀김", "situation": "혼자"}, "뼈 없이 간단하게 먹기 좋은 치킨"),
    menu("짜장면", "중식", {"craving": "면", "cuisine": "중식", "spice": "안매움", "soup": "없음", "flavor": "짭짤한", "main": "돼지", "noodle_style": "짜장", "cook": "볶음", "situation": "혼자"}, "빠르고 든든한 중식 기본 메뉴"),
    menu("간짜장", "중식", {"craving": "면", "cuisine": "중식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "돼지", "noodle_style": "짜장", "cook": "볶음", "situation": "혼자"}, "볶은 춘장 맛이 진한 짜장면"),
    menu("짬뽕", "중식", {"craving": "면", "cuisine": "중식", "spice": "얼큰", "soup": "면국물", "flavor": "매콤한", "main": "해산물", "noodle_style": "짬뽕", "cook": "볶음", "situation": "혼자"}, "얼큰한 국물과 면을 같이 먹는 중식 메뉴"),
    menu("백짬뽕", "중식", {"craving": "면", "cuisine": "중식", "spice": "안매움", "soup": "면국물", "flavor": "담백한", "main": "해산물", "noodle_style": "짬뽕", "cook": "볶음", "situation": "혼자"}, "맵지 않은 해산물 국물면"),
    menu("중식볶음밥", "중식", {"craving": "밥", "cuisine": "중식", "spice": "안매움", "soup": "없음", "flavor": "짭짤한", "main": "두부계란", "rice_style": "상관없음", "cook": "볶음", "situation": "혼자"}, "짜장 소스와 잘 맞는 중식 밥 메뉴"),
    menu("탕수육", "중식", {"craving": "고기", "cuisine": "중식", "spice": "안매움", "soup": "없음", "flavor": "달콤한", "main": "돼지", "meat_type": "돼지", "cook": "튀김", "situation": "여럿"}, "여럿이 나눠먹기 좋은 대표 중식"),
    menu("마라탕", "중식", {"craving": "국물", "cuisine": "중식", "spice": "마라", "soup": "탕국밥", "flavor": "매콤한", "main": "채소", "soup_style": "전골탕", "cook": "찜조림", "situation": "여럿"}, "마라 향과 국물이 강하게 당길 때 좋은 메뉴"),
    menu("마라샹궈", "중식", {"craving": "고기", "cuisine": "중식", "spice": "마라", "soup": "없음", "flavor": "매콤한", "main": "채소", "meat_type": "상관없음", "cook": "볶음", "situation": "여럿"}, "국물 없이 진한 마라 볶음이 당길 때"),
    menu("양꼬치", "중식", {"craving": "고기", "cuisine": "중식", "spice": "매콤", "soup": "없음", "flavor": "짭짤한", "main": "소", "meat_type": "소", "cook": "구이", "situation": "술안주"}, "술안주로 강한 향의 고기가 당길 때"),
    menu("피자", "피자", {"craving": "치킨피자", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "상관없음", "party_food": "피자", "cook": "구이", "situation": "여럿"}, "여럿이 나눠먹기 쉬운 배달 대표 메뉴"),
    menu("페퍼로니피자", "피자", {"craving": "치킨피자", "cuisine": "양식", "spice": "매콤", "soup": "없음", "flavor": "짭짤한", "main": "돼지", "party_food": "피자", "cook": "구이", "situation": "여럿"}, "짭짤한 토핑이 확실한 피자"),
    menu("불고기피자", "피자", {"craving": "치킨피자", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "달콤한", "main": "소", "party_food": "피자", "cook": "구이", "situation": "가족"}, "달콤짭짤해서 호불호가 적은 피자"),
    menu("고구마피자", "피자", {"craving": "치킨피자", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "달콤한", "main": "채소", "party_food": "피자", "cook": "구이", "situation": "둘이"}, "달콤하고 부드러운 피자"),
    menu("치즈피자", "피자", {"craving": "치킨피자", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "상관없음", "party_food": "피자", "cook": "구이", "situation": "혼자"}, "치즈 맛에 집중하고 싶을 때 좋은 피자"),
    menu("떡볶이", "분식", {"craving": "분식", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "매콤한", "main": "상관없음", "snack_style": "떡볶이", "cook": "볶음", "situation": "야식"}, "매콤하게 기분 전환하기 좋은 분식"),
    menu("로제떡볶이", "분식", {"craving": "분식", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "고소한", "main": "상관없음", "snack_style": "떡볶이", "cook": "볶음", "situation": "둘이"}, "부드럽고 매콤한 분식 메뉴"),
    menu("김밥", "분식", {"craving": "밥", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "담백한", "main": "채소", "rice_style": "김밥", "cook": "차가운", "situation": "혼자"}, "빠르고 부담 없는 한 끼"),
    menu("라면", "분식", {"craving": "면", "cuisine": "한식", "spice": "얼큰", "soup": "면국물", "flavor": "매콤한", "main": "상관없음", "noodle_style": "라멘우동", "cook": "찜조림", "situation": "야식"}, "간단하게 얼큰한 면이 당길 때"),
    menu("순대", "분식", {"craving": "분식", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "담백한", "main": "돼지", "snack_style": "순대", "cook": "찜조림", "situation": "술안주"}, "떡볶이와도 잘 맞는 담백한 분식"),
    menu("튀김", "분식", {"craving": "분식", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "상관없음", "snack_style": "튀김만두", "cook": "튀김", "situation": "여럿"}, "바삭한 간식형 분식"),
    menu("만두", "분식", {"craving": "분식", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "짭짤한", "main": "돼지", "snack_style": "튀김만두", "cook": "찜조림", "situation": "혼자"}, "가볍게 곁들이기 좋은 메뉴"),
    menu("족발", "족발보쌈", {"craving": "고기", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "짭짤한", "main": "돼지", "meat_type": "족발보쌈", "cook": "찜조림", "situation": "술안주"}, "쫀득한 고기 안주가 필요할 때"),
    menu("매운족발", "족발보쌈", {"craving": "고기", "cuisine": "한식", "spice": "매움", "soup": "없음", "flavor": "매콤한", "main": "돼지", "meat_type": "족발보쌈", "cook": "찜조림", "situation": "술안주"}, "매운 고기 안주가 당길 때"),
    menu("보쌈", "족발보쌈", {"craving": "고기", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "담백한", "main": "돼지", "meat_type": "족발보쌈", "cook": "찜조림", "situation": "가족"}, "자극이 덜하고 든든한 고기 메뉴"),
    menu("햄버거", "패스트푸드", {"craving": "치킨피자", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "짭짤한", "main": "소", "party_food": "버거", "cook": "구이", "situation": "혼자"}, "빠르고 든든한 한 끼"),
    menu("치킨버거", "패스트푸드", {"craving": "치킨피자", "cuisine": "양식", "spice": "매콤", "soup": "없음", "flavor": "매콤한", "main": "닭", "party_food": "버거", "cook": "튀김", "situation": "혼자"}, "치킨과 버거 둘 다 당길 때"),
    menu("샌드위치", "패스트푸드", {"craving": "분식", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "담백한", "main": "채소", "snack_style": "토스트핫도그", "cook": "차가운", "situation": "혼자"}, "가볍고 깔끔한 한 끼"),
    menu("토스트", "패스트푸드", {"craving": "분식", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "두부계란", "snack_style": "토스트핫도그", "cook": "구이", "situation": "혼자"}, "간단하게 허기를 채우기 좋은 메뉴"),
    menu("핫도그", "패스트푸드", {"craving": "분식", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "달콤한", "main": "돼지", "snack_style": "토스트핫도그", "cook": "튀김", "situation": "야식"}, "달고 짭짤한 간식형 메뉴"),
    menu("김치찌개", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "얼큰", "soup": "찌개", "flavor": "매콤한", "main": "돼지", "soup_style": "찌개", "cook": "찜조림", "situation": "가족"}, "밥과 같이 든든한 얼큰 찌개"),
    menu("된장찌개", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "안매움", "soup": "찌개", "flavor": "짭짤한", "main": "두부계란", "soup_style": "찌개", "cook": "찜조림", "situation": "가족"}, "구수하고 익숙한 한식 찌개"),
    menu("순두부찌개", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "매콤", "soup": "찌개", "flavor": "담백한", "main": "두부계란", "soup_style": "찌개", "cook": "찜조림", "situation": "혼자"}, "부드럽고 따뜻하게 먹기 좋은 국물 메뉴"),
    menu("부대찌개", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "매콤", "soup": "찌개", "flavor": "짭짤한", "main": "돼지", "soup_style": "찌개", "cook": "찜조림", "situation": "여럿"}, "햄과 국물이 든든한 찌개"),
    menu("감자탕", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "얼큰", "soup": "탕국밥", "flavor": "짭짤한", "main": "돼지", "soup_style": "해장국", "cook": "찜조림", "situation": "가족"}, "푸짐한 뼈고기와 얼큰한 국물"),
    menu("뼈해장국", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "얼큰", "soup": "탕국밥", "flavor": "담백한", "main": "돼지", "soup_style": "해장국", "cook": "찜조림", "situation": "혼자"}, "혼자서도 든든하게 먹는 해장국"),
    menu("설렁탕", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "안매움", "soup": "탕국밥", "flavor": "담백한", "main": "소", "soup_style": "맑은국물", "cook": "찜조림", "situation": "가족"}, "맵지 않고 든든한 탕 메뉴"),
    menu("육개장", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "얼큰", "soup": "탕국밥", "flavor": "매콤한", "main": "소", "soup_style": "해장국", "cook": "찜조림", "situation": "혼자"}, "얼큰한 소고기 국물 메뉴"),
    menu("돼지국밥", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "안매움", "soup": "탕국밥", "flavor": "짭짤한", "main": "돼지", "soup_style": "해장국", "cook": "찜조림", "situation": "혼자"}, "밥과 국물을 한 번에 먹는 든든한 메뉴"),
    menu("갈비탕", "찜탕찌개", {"craving": "국물", "cuisine": "한식", "spice": "안매움", "soup": "탕국밥", "flavor": "고소한", "main": "소", "soup_style": "맑은국물", "cook": "찜조림", "situation": "가족"}, "맑고 진한 소고기 탕"),
    menu("제육덮밥", "한식", {"craving": "밥", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "매콤한", "main": "돼지", "rice_style": "덮밥", "cook": "볶음", "situation": "혼자"}, "매콤한 고기와 밥 조합"),
    menu("비빔밥", "한식", {"craving": "밥", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "담백한", "main": "채소", "rice_style": "비빔밥", "cook": "볶음", "situation": "혼자"}, "채소와 밥을 같이 먹는 균형 잡힌 메뉴"),
    menu("불고기덮밥", "한식", {"craving": "밥", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "달콤한", "main": "소", "rice_style": "덮밥", "cook": "볶음", "situation": "혼자"}, "달달한 고기 덮밥"),
    menu("도시락", "한식", {"craving": "밥", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "짭짤한", "main": "상관없음", "rice_style": "백반", "cook": "볶음", "situation": "혼자"}, "여러 반찬을 한 번에 먹는 배달 한 끼"),
    menu("백반", "한식", {"craving": "밥", "cuisine": "한식", "spice": "안매움", "soup": "상관없음", "flavor": "담백한", "main": "상관없음", "rice_style": "백반", "cook": "찜조림", "situation": "가족"}, "익숙한 반찬과 밥이 당길 때"),
    menu("죽", "한식", {"craving": "밥", "cuisine": "한식", "spice": "안매움", "soup": "상관없음", "flavor": "담백한", "main": "상관없음", "rice_style": "죽", "cook": "찜조림", "situation": "혼자"}, "속이 편한 따뜻한 밥 메뉴"),
    menu("삼겹살", "한식", {"craving": "고기", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "돼지", "meat_type": "돼지", "cook": "구이", "situation": "여럿"}, "구운 돼지고기가 확실히 당길 때"),
    menu("소불고기", "한식", {"craving": "고기", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "달콤한", "main": "소", "meat_type": "소", "cook": "볶음", "situation": "가족"}, "달달한 소고기 메뉴"),
    menu("찜닭", "한식", {"craving": "고기", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "짭짤한", "main": "닭", "meat_type": "닭", "cook": "찜조림", "situation": "여럿"}, "양이 넉넉한 닭요리"),
    menu("닭볶음탕", "한식", {"craving": "고기", "cuisine": "한식", "spice": "얼큰", "soup": "찌개", "flavor": "매콤한", "main": "닭", "meat_type": "닭", "cook": "찜조림", "situation": "가족"}, "얼큰한 닭고기 국물 요리"),
    menu("닭갈비", "한식", {"craving": "고기", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "매콤한", "main": "닭", "meat_type": "닭", "cook": "볶음", "situation": "여럿"}, "볶음밥까지 이어가기 좋은 닭요리"),
    menu("곱창", "한식", {"craving": "고기", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "고소한", "main": "소", "meat_type": "소", "cook": "구이", "situation": "술안주"}, "고소한 안주형 고기가 당길 때"),
    menu("돈까스", "돈까스일식", {"craving": "고기", "cuisine": "일식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "돼지", "meat_type": "돼지", "cook": "튀김", "situation": "혼자"}, "바삭하고 든든한 실패 확률 낮은 메뉴"),
    menu("치즈돈까스", "돈까스일식", {"craving": "고기", "cuisine": "일식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "돼지", "meat_type": "돼지", "cook": "튀김", "situation": "둘이"}, "치즈가 들어간 바삭한 돈까스"),
    menu("카츠동", "돈까스일식", {"craving": "밥", "cuisine": "일식", "spice": "안매움", "soup": "없음", "flavor": "짭짤한", "main": "돼지", "rice_style": "덮밥", "cook": "튀김", "situation": "혼자"}, "돈까스와 밥을 같이 먹는 덮밥"),
    menu("초밥", "돈까스일식", {"craving": "밥", "cuisine": "일식", "spice": "안매움", "soup": "없음", "flavor": "새콤한", "main": "해산물", "rice_style": "상관없음", "cook": "생", "situation": "둘이"}, "깔끔하고 대화하기 좋은 외식 메뉴"),
    menu("연어덮밥", "돈까스일식", {"craving": "밥", "cuisine": "일식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "해산물", "rice_style": "덮밥", "cook": "생", "situation": "혼자"}, "깔끔하면서도 포만감 있는 덮밥"),
    menu("회덮밥", "돈까스일식", {"craving": "밥", "cuisine": "일식", "spice": "매콤", "soup": "없음", "flavor": "새콤한", "main": "해산물", "rice_style": "비빔밥", "cook": "생", "situation": "혼자"}, "새콤매콤한 해산물 밥 메뉴"),
    menu("라멘", "돈까스일식", {"craving": "면", "cuisine": "일식", "spice": "매콤", "soup": "면국물", "flavor": "고소한", "main": "돼지", "noodle_style": "라멘우동", "cook": "찜조림", "situation": "혼자"}, "진한 국물과 면이 당길 때"),
    menu("우동", "돈까스일식", {"craving": "면", "cuisine": "일식", "spice": "안매움", "soup": "면국물", "flavor": "담백한", "main": "상관없음", "noodle_style": "라멘우동", "cook": "찜조림", "situation": "야식"}, "따뜻하고 부담 적은 면 메뉴"),
    menu("규동", "돈까스일식", {"craving": "밥", "cuisine": "일식", "spice": "안매움", "soup": "없음", "flavor": "짭짤한", "main": "소", "rice_style": "덮밥", "cook": "볶음", "situation": "혼자"}, "소고기 덮밥이 빠르게 당길 때"),
    menu("회", "해산물", {"craving": "고기", "cuisine": "일식", "spice": "안매움", "soup": "없음", "flavor": "담백한", "main": "해산물", "meat_type": "고기말고", "cook": "생", "situation": "술안주"}, "깔끔한 해산물 안주"),
    menu("물회", "해산물", {"craving": "국물", "cuisine": "한식", "spice": "매콤", "soup": "탕국밥", "flavor": "새콤한", "main": "해산물", "soup_style": "해물탕", "cook": "차가운", "situation": "둘이"}, "새콤하고 시원한 해산물 메뉴"),
    menu("아구찜", "해산물", {"craving": "고기", "cuisine": "한식", "spice": "매움", "soup": "없음", "flavor": "매콤한", "main": "해산물", "meat_type": "고기말고", "cook": "찜조림", "situation": "가족"}, "매콤한 해산물 찜"),
    menu("해물찜", "해산물", {"craving": "고기", "cuisine": "한식", "spice": "매콤", "soup": "없음", "flavor": "짭짤한", "main": "해산물", "meat_type": "고기말고", "cook": "찜조림", "situation": "여럿"}, "여럿이 먹기 좋은 해산물 찜"),
    menu("생선구이", "해산물", {"craving": "고기", "cuisine": "한식", "spice": "안매움", "soup": "없음", "flavor": "담백한", "main": "해산물", "meat_type": "고기말고", "cook": "구이", "situation": "가족"}, "담백한 단백질이 당길 때"),
    menu("파스타", "아시안양식", {"craving": "면", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "상관없음", "noodle_style": "파스타", "cook": "볶음", "situation": "둘이"}, "부드러운 양식 면 메뉴"),
    menu("매운파스타", "아시안양식", {"craving": "면", "cuisine": "양식", "spice": "매콤", "soup": "없음", "flavor": "매콤한", "main": "상관없음", "noodle_style": "파스타", "cook": "볶음", "situation": "둘이"}, "느끼함이 덜한 매콤한 파스타"),
    menu("리조또", "아시안양식", {"craving": "밥", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "상관없음", "rice_style": "상관없음", "cook": "볶음", "situation": "둘이"}, "크리미한 밥 메뉴가 당길 때"),
    menu("샐러드", "아시안양식", {"craving": "밥", "cuisine": "양식", "spice": "안매움", "soup": "없음", "flavor": "담백한", "main": "채소", "rice_style": "상관없음", "cook": "차가운", "situation": "혼자"}, "가볍고 깔끔한 식사"),
    menu("포케", "아시안양식", {"craving": "밥", "cuisine": "기타", "spice": "안매움", "soup": "없음", "flavor": "새콤한", "main": "해산물", "rice_style": "비빔밥", "cook": "차가운", "situation": "혼자"}, "깔끔하지만 허전하지 않은 한 끼"),
    menu("쌀국수", "아시안양식", {"craving": "면", "cuisine": "기타", "spice": "안매움", "soup": "면국물", "flavor": "담백한", "main": "소", "noodle_style": "아시안면", "cook": "찜조림", "situation": "혼자"}, "따뜻하고 깔끔한 면 메뉴"),
    menu("분짜", "아시안양식", {"craving": "면", "cuisine": "기타", "spice": "안매움", "soup": "없음", "flavor": "새콤한", "main": "돼지", "noodle_style": "아시안면", "cook": "차가운", "situation": "둘이"}, "상큼하고 가벼운 아시안 면"),
    menu("타코", "아시안양식", {"craving": "고기", "cuisine": "기타", "spice": "매콤", "soup": "없음", "flavor": "새콤한", "main": "소", "meat_type": "소", "cook": "구이", "situation": "둘이"}, "가볍고 색다른 고기 메뉴"),
    menu("커피", "카페디저트", {"craving": "디저트", "cuisine": "기타", "spice": "안매움", "soup": "없음", "flavor": "담백한", "main": "상관없음", "dessert_type": "커피", "cook": "차가운", "situation": "혼자"}, "식사보다 카페 메뉴가 필요할 때"),
    menu("케이크", "카페디저트", {"craving": "디저트", "cuisine": "기타", "spice": "안매움", "soup": "없음", "flavor": "달콤한", "main": "상관없음", "dessert_type": "빵케이크", "cook": "차가운", "situation": "둘이"}, "달콤한 디저트가 당길 때"),
    menu("와플", "카페디저트", {"craving": "디저트", "cuisine": "기타", "spice": "안매움", "soup": "없음", "flavor": "고소한", "main": "상관없음", "dessert_type": "빵케이크", "cook": "구이", "situation": "야식"}, "바삭하고 달콤한 디저트"),
    menu("빙수", "카페디저트", {"craving": "디저트", "cuisine": "기타", "spice": "안매움", "soup": "없음", "flavor": "달콤한", "main": "상관없음", "dessert_type": "빙수", "cook": "차가운", "situation": "여럿"}, "시원하고 달콤하게 나눠먹는 메뉴"),
    menu("아이스크림", "카페디저트", {"craving": "디저트", "cuisine": "기타", "spice": "안매움", "soup": "없음", "flavor": "달콤한", "main": "상관없음", "dessert_type": "아이스크림", "cook": "차가운", "situation": "혼자"}, "가볍게 달콤한 게 필요할 때"),
    menu("과일컵", "카페디저트", {"craving": "디저트", "cuisine": "기타", "spice": "안매움", "soup": "없음", "flavor": "새콤한", "main": "채소", "dessert_type": "과일", "cook": "차가운", "situation": "혼자"}, "상큼하고 가벼운 디저트"),
]


def answer_profile_for_menu(menu_item: Dict[str, Any]) -> Dict[str, str]:
    return dict(menu_item["profile"])


def question_is_available(question: Dict[str, Any], answers: Dict[str, str]) -> bool:
    condition = question.get("condition")
    if not condition:
        return True
    return all(answers.get(key) == value for key, value in condition.items())


def score_menu(menu_item: Dict[str, Any], answers: Dict[str, str]) -> float:
    profile = menu_item["profile"]
    score = 0.0
    matched = 0

    for key, selected in answers.items():
        if key == "avoid":
            score += avoid_penalty(menu_item, selected)
            continue

        expected = profile.get(key)
        if expected is None:
            continue

        if selected == expected:
            score += QUESTION_WEIGHTS.get(key, 1.0)
            matched += 1
        elif selected in {"상관없음", "기타"} and expected in {selected, "상관없음", "기타"}:
            score += QUESTION_WEIGHTS.get(key, 1.0) * 0.4

    if answers and matched == len([key for key in answers if key != "avoid" and key in profile]):
        score += 0.001 * len(profile)

    return score


def avoid_penalty(menu_item: Dict[str, Any], selected: str) -> float:
    if selected == "없음":
        return 0.3

    profile = menu_item["profile"]
    tags = set(menu_item.get("tags", []))
    penalties = {
        "매운거": profile.get("spice") in {"매콤", "얼큰", "매움", "마라"},
        "기름진거": profile.get("cook") in {"튀김", "구이"} or profile.get("flavor") == "고소한",
        "밀가루": profile.get("craving") in {"면", "분식", "치킨피자", "디저트"} or profile.get("noodle_style") is not None,
        "해산물": profile.get("main") == "해산물" or "해산물" in tags,
    }
    return -8.0 if penalties.get(selected, False) else 1.0


def recommend_delivery_food(
    answers: Dict[str, str],
    exclude_names: Optional[List[str]] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    exclude_set = set(exclude_names or [])
    scored = [
        (score_menu(menu_item, answers), menu_item)
        for menu_item in DELIVERY_MENUS
        if menu_item["name"] not in exclude_set
    ]
    scored.sort(key=lambda item: (-item[0], item[1]["name"]))

    return [
        {
            "name": menu_item["name"],
            "score": round(score, 3),
            "short_desc": menu_item["short_desc"],
            "category": menu_item["category"],
            "delivery_category": menu_item["delivery_category"],
            "tags": menu_item["tags"],
        }
        for score, menu_item in scored[:limit]
    ]


def choose_next_question(answers: Dict[str, str], asked_keys: Set[str]) -> Optional[Dict[str, Any]]:
    specialized_key = SPECIALIZED_BY_CRAVING.get(answers.get("craving"))
    if specialized_key and specialized_key not in asked_keys:
        return QUESTION_BY_KEY[specialized_key]

    for key in EARLY_PRIORITY_KEYS:
        question = QUESTION_BY_KEY[key]
        if key not in asked_keys and question_is_available(question, answers):
            return question

    candidates = [
        question
        for question in DELIVERY_QUESTIONS
        if question["key"] not in asked_keys and question_is_available(question, answers)
    ]
    if not candidates:
        return None

    top_candidates = recommend_delivery_food(answers, limit=min(20, len(DELIVERY_MENUS)))
    top_names = {item["name"] for item in top_candidates}
    top_menus = [menu_item for menu_item in DELIVERY_MENUS if menu_item["name"] in top_names]

    return max(candidates, key=lambda question: question_split_score(question, top_menus))


def question_split_score(question: Dict[str, Any], menu_items: List[Dict[str, Any]]) -> float:
    key = question["key"]
    buckets: Counter[str] = Counter()

    for menu_item in menu_items:
        value = menu_item["profile"].get(key)
        if value in question["options"]:
            buckets[value] += 1

    if not buckets:
        return 0.0

    return entropy(buckets) + len(buckets) * 0.12


def entropy(buckets: Counter[str]) -> float:
    total = sum(buckets.values())
    if total == 0:
        return 0.0
    result = 0.0
    for count in buckets.values():
        probability = count / total
        result -= probability * log2(probability)
    return result


def simulate_profile_winners() -> Dict[str, int]:
    winners: Counter[str] = Counter()
    for menu_item in DELIVERY_MENUS:
        answers = answer_profile_for_menu(menu_item)
        winner = recommend_delivery_food(answers, limit=1)[0]["name"]
        winners[winner] += 1
    return dict(winners)
