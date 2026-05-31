import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


DEFAULT_BASE_URL = "https://picky-chatbot-production.up.railway.app"
DEFAULT_OUTPUT = Path("docs/kakao-today-growth-brief.md")

CAMPAIGNS = [
    {
        "key": "threads_lunch",
        "keyword": "점심추천",
        "angle": "점심 메뉴 결정 시간을 줄이는 사람",
        "asset": "static/promo/kakao-threads-lunch.png",
        "post": (
            "오늘 점심 뭐 먹을지 정하는 데 10분 쓰는 사람들 많지 않나.\n\n"
            "카톡에서 Picky한테 `점심추천` 보내면 상황 몇 개 고르고 메뉴 후보 3개를 바로 받을 수 있음.\n\n"
            "써보고 추천이 납득되는지 알려줘."
        ),
        "video": "점심 뭐 먹지? -> 카톡 Picky -> `점심추천` -> 빠르게 선택지 탭 -> 추천 카드 3개",
    },
    {
        "key": "threads_solo",
        "keyword": "혼밥추천",
        "angle": "혼밥 메뉴를 못 고르는 사람",
        "asset": "static/promo/kakao-story-solo.png",
        "post": (
            "혼밥 메뉴 고르는 게 은근 제일 어렵다.\n"
            "너무 무겁긴 싫고, 또 너무 대충 먹긴 싫고.\n\n"
            "카톡에서 Picky한테 `혼밥추천` 보내면 오늘 상황에 맞춰 후보 3개를 뽑아줌."
        ),
        "video": "혼밥인데 뭐 먹지? -> `혼밥추천` 입력 -> 든든/가볍게 선택 -> 결과 카드",
    },
    {
        "key": "threads_dinner",
        "keyword": "저녁추천",
        "angle": "저녁 메뉴를 배달앱에서 오래 고르는 사람",
        "asset": "static/promo/kakao-build-log.png",
        "post": (
            "저녁 메뉴 못 정해서 배달앱만 20분 보는 사람들을 위한 봇 만들었다.\n\n"
            "카톡에서 Picky한테 `저녁추천` 보내면 몇 번 누르고 메뉴 후보를 받을 수 있음.\n"
            "별로면 다시 추천도 가능."
        ),
        "video": "배달앱 스크롤 20분 -> 카톡 Picky -> `저녁추천` -> 별로 버튼으로 후보 교체",
    },
    {
        "key": "brand",
        "keyword": "피키추천",
        "angle": "첫 1,000명 공개 빌드 로그",
        "asset": "static/promo/kakao-build-log.png",
        "post": (
            "카톡에서 메뉴 추천해주는 작은 봇을 만들고 있다.\n\n"
            "목표는 첫 1,000명. 지금은 캐릭터 카드, 짧은 선택지, 추천 피드백, 공유 문구까지 붙였다.\n\n"
            "카톡에서 Picky 열고 `피키추천`."
        ),
        "video": "Picky 캐릭터 카드 -> 짧은 선택지 -> 음식 추천 카드 -> 1,000명 목표 화면",
    },
]


def number(value: Any, default: int | float = 0) -> int | float:
    return default if value is None else value


def comma(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def select_focus_campaign(kakao: dict[str, Any]) -> dict[str, str]:
    campaign_starts = kakao.get("campaignStarts") or {}

    if campaign_starts:
        known_campaigns = [campaign for campaign in CAMPAIGNS if campaign["key"] in campaign_starts]
        if known_campaigns:
            return max(known_campaigns, key=lambda campaign: int(campaign_starts.get(campaign["key"], 0)))

    unique_users = int(number(kakao.get("uniqueUsers"), 0))
    if unique_users < 50:
        return CAMPAIGNS[0]

    return CAMPAIGNS[-1]


def build_reply_sprint(keyword: str) -> list[str]:
    return [
        f"오늘 뭐 먹지 고민이면 카톡 Picky에서 `{keyword}` 보내면 바로 후보 나와요.",
        f"배달앱 켜기 전에 Picky한테 `{keyword}` 한 번 보내보세요. 7개만 고르면 됩니다.",
        f"저도 메뉴 못 고르는 문제 때문에 만든 봇인데, 시작어는 `{keyword}`입니다.",
        f"추천이 별로면 `별로` 누르면 다른 후보도 나와요. 카톡 Picky `{keyword}`.",
        f"친구랑 정하기 어려울 때 각자 Picky 추천 받아보고 겹치는 메뉴로 가도 괜찮아요. `{keyword}`",
        f"혼자 고민하지 말고 카톡에서 Picky 열고 `{keyword}` 보내보세요.",
        f"상황/맛/매운 정도만 고르면 메뉴 3개 줍니다. 시작어는 `{keyword}`.",
        f"점심 시간 짧으면 카톡 Picky가 빠릅니다. 시작어는 `{keyword}`.",
        f"오늘은 메뉴 고르는 시간을 줄여보세요. 카톡 Picky에서 `{keyword}`.",
        f"써보고 이상한 추천 나오면 피드백도 주세요. 카톡 Picky `{keyword}`.",
    ]


def build_growth_brief(
    kakao: dict[str, Any],
    toss: dict[str, Any],
    timestamp: str,
    note: str = "",
) -> str:
    campaign = select_focus_campaign(kakao)
    kakao_events = kakao.get("events") or {}
    toss_events = toss.get("events") or {}
    kakao_starts = int(number(kakao_events.get("kakao_start"), 0))
    kakao_completions = int(number(kakao_events.get("kakao_recommendation_completed"), 0))
    completion_rate = float(number(kakao.get("completionRate"), 0.0))
    feedback_rate = float(number(kakao.get("feedbackRate"), 0.0))
    replies = "\n".join(f"{index}. {reply}" for index, reply in enumerate(build_reply_sprint(campaign["keyword"]), 1))

    watch_items = []
    if kakao_starts == 0:
        watch_items.append("- First target: get the first 10 Kakao starts, then judge completion and feedback rates.")
    elif completion_rate < 55.0:
        watch_items.append("- Kakao completion rate is below 55%; after posting, inspect where users stop and shorten confusing copy.")

    if kakao_starts > 0 and feedback_rate < 10.0:
        watch_items.append("- Kakao feedback rate is below 10%; ask users to press `결정`, `비슷한`, or `별로` in the post copy.")
    if kakao_completions >= 10 and int(number(kakao_events.get("kakao_share_prompt"), 0)) == 0:
        watch_items.append("- Share prompts are 0; today's post should explicitly ask users to tap `공유` after results.")

    watch_text = "\n".join(watch_items) if watch_items else "- No immediate funnel warning. Repeat the best-performing angle."

    return f"""# Picky Daily Growth Brief

Generated: {timestamp}
Note: {note or "daily-growth"}

## Scoreboard

- Kakao: {comma(kakao.get("uniqueUsers"))} / {comma(kakao.get("targetUsers", 1000))} users, {comma(kakao.get("remainingUsers"))} remaining
- Kakao starts: {comma(kakao_events.get("kakao_start"))}
- Kakao completions: {comma(kakao_events.get("kakao_recommendation_completed"))}
- Kakao share prompts: {comma(kakao_events.get("kakao_share_prompt"))}
- Toss: {comma(number(toss.get("uniqueUsers"), 0))} users, {comma(number(toss_events.get("share_clicked"), 0))} shares

## Focus

- Focus keyword: `{campaign["keyword"]}`
- Campaign key: `{campaign["key"]}`
- Angle: {campaign["angle"]}
- Asset: `{campaign["asset"]}`

## Threads Post

{campaign["post"]}

## Reply Sprint

Reply to 10 relevant food-decision posts with these non-spammy variants:

{replies}

## Short Video

- Shot list: {campaign["video"]}
- Caption: 카톡에서 Picky 열고 `{campaign["keyword"]}`
- End frame: 추천 카드가 뜬 화면 + `공유` 버튼 안내

## Funnel Watch

{watch_text}

## Measure Again

Run these after posting and replying:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\check_growth_metrics.ps1
.\\.venv\\Scripts\\python.exe scripts\\log_growth_snapshot.py --note "daily-brief-after-post"
```
"""


def fetch_json(url: str) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc


def current_timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate today's Picky growth execution brief.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Markdown output path")
    parser.add_argument("--note", default="", help="Optional note for this brief")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    base_url = args.base_url.rstrip("/")
    kakao = fetch_json(f"{base_url}/api/kakao/growth")
    toss = fetch_json(f"{base_url}/api/toss/metrics")
    brief = build_growth_brief(kakao, toss, current_timestamp(), args.note)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(brief, encoding="utf-8")
    print(f"Growth brief written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
