# Picky Daily Growth Brief

Generated: 2026-05-31T23:19:48+09:00
Note: prod-growth-loop

## Scoreboard

- Kakao: 0 / 1,000 users, 1,000 remaining
- Kakao starts: 0
- Kakao completions: 0
- Kakao share prompts: 0
- Toss: 0 users, 0 shares

## Focus

- Focus keyword: `점심추천`
- Campaign key: `threads_lunch`
- Angle: 점심 메뉴 결정 시간을 줄이는 사람
- Asset: `static/promo/kakao-threads-lunch.png`

## Threads Post

오늘 점심 뭐 먹을지 정하는 데 10분 쓰는 사람들 많지 않나.

카톡에서 Picky한테 `점심추천` 보내면 상황 몇 개 고르고 메뉴 후보 3개를 바로 받을 수 있음.

써보고 추천이 납득되는지 알려줘.

## Reply Sprint

Reply to 10 relevant food-decision posts with these non-spammy variants:

1. 오늘 뭐 먹지 고민이면 카톡 Picky에서 `점심추천` 보내면 바로 후보 나와요.
2. 배달앱 켜기 전에 Picky한테 `점심추천` 한 번 보내보세요. 7개만 고르면 됩니다.
3. 저도 메뉴 못 고르는 문제 때문에 만든 봇인데, 시작어는 `점심추천`입니다.
4. 추천이 별로면 `별로` 누르면 다른 후보도 나와요. 카톡 Picky `점심추천`.
5. 친구랑 정하기 어려울 때 각자 Picky 추천 받아보고 겹치는 메뉴로 가도 괜찮아요. `점심추천`
6. 혼자 고민하지 말고 카톡에서 Picky 열고 `점심추천` 보내보세요.
7. 상황/맛/매운 정도만 고르면 메뉴 3개 줍니다. 시작어는 `점심추천`.
8. 점심 시간 짧으면 카톡 Picky가 빠릅니다. 시작어는 `점심추천`.
9. 오늘은 메뉴 고르는 시간을 줄여보세요. 카톡 Picky에서 `점심추천`.
10. 써보고 이상한 추천 나오면 피드백도 주세요. 카톡 Picky `점심추천`.

## Short Video

- Shot list: 점심 뭐 먹지? -> 카톡 Picky -> `점심추천` -> 빠르게 선택지 탭 -> 추천 카드 3개
- Caption: 카톡에서 Picky 열고 `점심추천`
- End frame: 추천 카드가 뜬 화면 + `공유` 버튼 안내

## Funnel Watch

- First target: get the first 10 Kakao starts, then judge completion and feedback rates.

## Measure Again

Run these after posting and replying:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_growth_metrics.ps1
.\.venv\Scripts\python.exe scripts\log_growth_snapshot.py --note "daily-brief-after-post"
```
