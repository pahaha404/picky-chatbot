# Kakao Day 1 Launch Pack

Use this as the first-day execution pack for getting the first 50 Picky Kakao chatbot users.

Primary CTA: open the Kakao Picky channel and send one exact keyword.

- Lunch: `점심추천`
- Dinner: `저녁추천`
- Solo meal: `혼밥추천`
- General test: `피키추천`

## Day 1 Target

- 50 unique users in `/api/kakao/growth`
- At least 30 recommendation completions
- At least 5 feedback clicks
- No Kakao Open Builder response errors

## 90-Minute Launch Sequence

1. Minute 0-10: Open `/api/kakao/growth` and record the starting numbers.
   You can also save a CSV snapshot:
   `.\.venv\Scripts\python.exe scripts\log_growth_snapshot.py --note "day1-start"`
2. Minute 10-20: Publish the pinned build-in-public post.
3. Minute 20-35: Send the friend/group test message to 10-20 people who can try it immediately.
4. Minute 35-55: Publish the lunch or dinner Threads post, depending on the time of day.
5. Minute 55-75: Reply to 10 relevant food-decision posts with the soft-reply templates below.
6. Minute 75-90: Check `/api/kakao/growth`, then write down starts, completions, completion rate, and the best keyword.
   Save another CSV snapshot:
   `.\.venv\Scripts\python.exe scripts\log_growth_snapshot.py --note "day1-90min"`

## Pinned Post

카톡에서 메뉴 추천해주는 작은 봇을 만들고 있습니다.

이름은 Picky.
상황이랑 취향 몇 개만 고르면 오늘 먹을 메뉴 후보 3개를 골라줘요.

목표는 첫 1,000명입니다.
지금은 50명 테스트부터 해보려고 합니다.

써보고 이상한 점 있으면 진짜 도움 됩니다.
카톡에서 Picky 열고 `피키추천` 입력하면 바로 시작됩니다.

Image: `static/promo/kakao-build-log.png`

## Time-Based Threads Posts

### Lunch

오늘 점심 뭐 먹지?

이거 매일 고민하는 게 귀찮아서 카톡 봇으로 만들었습니다.
Picky한테 `점심추천` 보내면 7개만 고르고 메뉴 후보 3개 받습니다.

첫 50명 테스트 중이라 피드백이 더 중요합니다.
써보고 추천이 이상하면 그대로 알려주세요.

Image: `static/promo/kakao-threads-lunch.png`

### Dinner

저녁 메뉴 못 정해서 배달앱만 계속 보는 사람들을 위한 카톡 봇을 만들었습니다.

Picky한테 `저녁추천` 보내면 상황/맛/먹는 방식 기준으로 메뉴 후보 3개를 뽑아줍니다.
별로면 바로 다른 메뉴도 볼 수 있습니다.

오늘 테스트해줄 사람 구합니다.

### Solo Meal

혼밥 메뉴 고르는 게 은근 제일 어렵습니다.
너무 무겁긴 싫고, 또 너무 대충 먹긴 싫고.

카톡에서 Picky한테 `혼밥추천` 보내면 몇 번 누르고 메뉴 후보를 받을 수 있습니다.
첫 50명 테스트 중입니다.

Image: `static/promo/kakao-story-solo.png`

## Friend Or Group Message

메뉴 추천 카톡 봇 하나 만들었는데 오늘 테스트 좀 해줄 수 있어?

카톡에서 Picky 열고 `피키추천` 보내면 바로 시작돼.
7개만 누르면 메뉴 3개 추천해주고, 별로면 다시 추천도 돼.

지금 필요한 피드백은 이거야:

1. 질문이 헷갈리는지
2. 선택지가 너무 긴지
3. 추천 메뉴가 납득되는지
4. 카드 이미지가 잘 보이는지

## Soft Reply Templates

Use these only when someone is already talking about food decisions. Do not spam unrelated posts.

1. 점심 못 고르는 글이면:
   카톡 메뉴 추천 봇 테스트 중인데 이런 상황에 딱 맞을 수도 있어요. Picky에서 `점심추천` 보내면 후보 3개 뽑아줍니다.

2. 배달앱 고민 글이면:
   배달앱 들어가기 전에 후보만 좁히는 용도로 만든 카톡 봇이 있어요. Picky에서 `저녁추천` 보내면 됩니다.

3. 혼밥 글이면:
   혼밥 메뉴 고르기용으로 Picky라는 카톡 봇 만들고 있어요. `혼밥추천` 보내면 몇 번 누르고 메뉴 추천 받아볼 수 있습니다.

4. 데이트 메뉴 글이면:
   데이트 메뉴 고르는 흐름도 넣어뒀어요. Picky에서 `데이트메뉴` 보내면 무난한 후보를 골라줍니다.

5. 피드백 요청형:
   지금 첫 50명 테스트 중이라 써보고 불편한 점 알려주면 바로 고칠게요. 카톡 Picky에서 `피키추천`입니다.

## 20-Second Video Script

Format: phone screen recording plus one caption track.

Shots:

1. 0-2s: Text overlay: "오늘 뭐 먹지?"
2. 2-4s: Open Kakao Picky chat.
3. 4-6s: Type `점심추천`.
4. 6-12s: Tap quick replies quickly.
5. 12-17s: Show recommendation card carousel.
6. 17-20s: Tap `비슷한` or `별로`.

Caption:

카톡에서 메뉴 골라주는 봇 만들었습니다.
Picky한테 `점심추천` 보내면 메뉴 후보 3개를 골라줘요.
첫 50명 테스트 중이라 피드백 받습니다.

## Day 1 Metric Check

Open:

```text
https://picky-chatbot-production.up.railway.app/api/kakao/growth
```

Quick terminal check:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_growth_metrics.ps1
```

Append a CSV snapshot:

```powershell
.\.venv\Scripts\python.exe scripts\log_growth_snapshot.py --note "day1-check"
```

Record:

| Time | uniqueUsers | kakao_start | kakao_recommendation_completed | completionRate | top campaign | Notes |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Start |  |  |  |  |  |  |
| +90 min |  |  |  |  |  |  |
| End of day |  |  |  |  |  |  |

## Decision Rules

- If `uniqueUsers` is below 10 after 90 minutes: DM 10 more direct testers before posting more public content.
- If `completionRate` is below 55%: watch the Kakao chat flow and shorten the confusing question or choice labels.
- If feedback clicks are 0 after 30 completions: ask testers directly to press `비슷한` or `별로` once.
- If one campaign keyword gets at least 2x more starts than others: post 3 more variations around that same use case the next day.
