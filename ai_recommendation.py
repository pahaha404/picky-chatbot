from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List, Optional


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_AI_MODEL = "gpt-5-nano"
AI_MODEL_ENV = "PICKY_AI_MODEL"
AI_ENABLED_ENV = "PICKY_AI_RECOMMENDATION_ENABLED"


AI_RECOMMENDATION_INSTRUCTIONS = """
너는 카카오톡 음식 추천 챗봇 Picky의 메뉴 추천 엔진이다.
목표는 사용자가 직접 메뉴를 고르게 하지 않고, 짧은 질문으로 취향을 추론해 최종 메뉴를 추천하는 것이다.

반드시 JSON 객체 하나만 출력한다. Markdown, 설명문, 코드블록은 금지한다.

출력 형식은 둘 중 하나다.
1. 질문:
{
  "action": "ask",
  "question": "짧은 한국어 질문",
  "options": ["짧은 선택지", "..."]
}
2. 추천:
{
  "action": "recommend",
  "recommendations": [
    {
      "name": "카탈로그에 있는 정확한 메뉴명",
      "short_desc": "짧은 설명",
      "reason": "왜 이 메뉴인지 한 문장"
    }
  ]
}

질문 규칙:
- 질문은 최대 4번만 한다. 이미 충분하면 바로 추천한다.
- 선택지는 4~6개로 만든다.
- 선택지에는 구체 메뉴명을 넣지 않는다. 예: 떡볶이, 짜장면, 피자, 치킨, 김치찌개 같은 이름은 금지.
- 선택지는 취향 판단에 도움되는 기준이어야 한다. 예: 매콤한, 담백한, 국물, 바삭한, 든든한, 가볍게.
- "기타"와 "상관없음"은 같은 질문에 함께 넣지 않는다.
- 카테고리/계열을 묻는 질문에는 "기타"를 쓰고, 취향 무관을 허용하는 질문에는 "상관없음"을 쓴다.
- "먹기 싫은 건?", "피하고 싶은 건?"처럼 제외 대상을 묻는 질문에는 "상관없음"이나 "기타"를 쓰지 않고 "없음"만 쓴다.
- 사용자가 구체 메뉴명을 직접 말하면 추가 질문 없이 그 메뉴를 1순위로 추천한다.

추천 규칙:
- recommendations[0]은 가장 납득도 높은 메뉴여야 한다.
- name은 반드시 제공된 menu_catalog 안의 name과 정확히 일치해야 한다.
- 추천은 최대 3개다.
- reason에는 사용자의 답변과 연결되는 근거를 쓴다.
- 사용자가 싫다고 한 것은 피한다.
""".strip()


DISLIKE_QUESTION_KEYWORDS = ("싫", "피하", "제외", "안 먹", "못 먹")
CATEGORY_QUESTION_KEYWORDS = ("계열", "종류", "카테고리")


def ai_recommendation_enabled() -> bool:
    value = os.getenv(AI_ENABLED_ENV, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def ai_model_name() -> str:
    return os.getenv(AI_MODEL_ENV, DEFAULT_AI_MODEL).strip() or DEFAULT_AI_MODEL


def compact_menu_catalog(menu_items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    catalog = []
    for item in menu_items:
        catalog.append(
            {
                "name": item.get("name"),
                "category": item.get("delivery_category") or item.get("category"),
                "description": item.get("short_desc", ""),
                "tags": list(item.get("tags", []))[:8],
            }
        )
    return catalog


def build_ai_recommendation_context(
    history: List[Dict[str, str]],
    menu_items: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "history": history[-10:],
        "menu_catalog": compact_menu_catalog(menu_items),
        "response_language": "ko",
    }


def normalize_ai_options(question: str, options: Iterable[str]) -> List[str]:
    normalized_options = list(
        dict.fromkeys(str(option).strip() for option in options if str(option).strip())
    )
    if any(keyword in question for keyword in DISLIKE_QUESTION_KEYWORDS):
        normalized_options = [
            option
            for option in normalized_options
            if option not in {"상관없음", "기타"}
        ]
        if "없음" not in normalized_options:
            normalized_options.append("없음")
        return normalized_options

    has_anything = "상관없음" in normalized_options
    has_other = "기타" in normalized_options
    if has_anything and has_other:
        keep = (
            "기타"
            if any(keyword in question for keyword in CATEGORY_QUESTION_KEYWORDS)
            else "상관없음"
        )
        drop = "상관없음" if keep == "기타" else "기타"
        normalized_options = [
            option for option in normalized_options if option != drop
        ]
    return normalized_options


def parse_ai_turn(raw_text: str) -> Dict[str, Any]:
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object")

    action = data.get("action")
    if action not in {"ask", "recommend"}:
        raise ValueError("AI response action must be ask or recommend")

    if action == "ask":
        question = str(data.get("question", "")).strip()
        options = data.get("options", [])
        if not question or not isinstance(options, list):
            raise ValueError("AI ask response requires question and options")
        return {
            "action": "ask",
            "question": question,
            "options": normalize_ai_options(question, options),
        }

    recommendations = data.get("recommendations", [])
    if not isinstance(recommendations, list):
        raise ValueError("AI recommend response requires recommendations")
    return {
        "action": "recommend",
        "recommendations": [
            recommendation
            for recommendation in recommendations
            if isinstance(recommendation, dict) and str(recommendation.get("name", "")).strip()
        ],
    }


def extract_response_text(response_data: Dict[str, Any]) -> str:
    output_text = response_data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: List[str] = []
    for output_item in response_data.get("output", []):
        for content_item in output_item.get("content", []):
            text = content_item.get("text")
            if isinstance(text, str):
                chunks.append(text)

    text = "".join(chunks).strip()
    if not text:
        raise ValueError("OpenAI response did not contain text")
    return text


def request_ai_recommendation_turn(
    history: List[Dict[str, str]],
    menu_items: Iterable[Dict[str, Any]],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for AI recommendation flow")

    context = build_ai_recommendation_context(history, menu_items)
    payload = {
        "model": model or ai_model_name(),
        "instructions": AI_RECOMMENDATION_INSTRUCTIONS,
        "input": json.dumps(context, ensure_ascii=False),
        "max_output_tokens": 900,
    }
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resolved_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    return parse_ai_turn(extract_response_text(response_data))
