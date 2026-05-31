# Kakao 1,000 User Growth Campaign

## Goal

Bring the Picky Kakao chatbot to 1,000 unique users and measure the path from first message to recommendation completion.

Primary metric:

- `/api/kakao/growth` `uniqueUsers`

Supporting metrics:

- `completionRate`: `kakao_recommendation_completed / kakao_start`
- `feedbackRate`: `kakao_feedback_clicked / kakao_recommendation_completed`
- `campaignStarts`: start count by campaign keyword

## Campaign Keywords

Use these exact Kakao start messages in content CTAs. They start the chatbot and are tracked in `/api/kakao/growth`.

| CTA keyword | Campaign key | Use case |
| --- | --- | --- |
| `점심추천` | `threads_lunch` | lunch posts, school/work meal decision |
| `저녁추천` | `threads_dinner` | dinner posts |
| `혼밥추천` | `threads_solo` | solo eating posts |
| `데이트메뉴` | `threads_date` | date/menu dilemma posts |
| `야식추천` | `threads_late_night` | late-night snack posts |
| `피키추천` | `brand` | general profile bio, pinned post |

Default organic starts such as `오늘 뭐 먹지`, `메뉴추천`, and `추천` are tracked as `organic`.

## 30-Day Funnel Targets

| Period | Unique users | Main action | Pass condition |
| --- | ---: | --- | --- |
| Days 1-3 | 50 | soft launch to friends, school/work groups, small Threads posts | no broken Kakao responses |
| Days 4-10 | 200 | daily Threads post + 2 short videos | completion rate at least 55% |
| Days 11-20 | 500 | repeat best-performing topic, add comments/replies CTA | feedback rate at least 10% |
| Days 21-30 | 1,000 | double down on top campaign keyword | 1,000 unique users reached |

## Threads Posts

## Promo Image Assets

Generated assets:

| Asset | Format | Use |
| --- | --- | --- |
| `static/promo/kakao-threads-lunch.png` | 1080 x 1350 | Threads post image for `점심추천` |
| `static/promo/kakao-story-solo.png` | 1080 x 1920 | Reels/Shorts/Story cover for `혼밥추천` |
| `static/promo/kakao-build-log.png` | 1080 x 1350 | Build-in-public post image for `피키추천` |

Regenerate them after changing Picky artwork or copy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_kakao_promo_assets.ps1
```

### 1. Lunch Decision

오늘 점심 뭐 먹을지 정하는 데 10분 쓰는 사람들 많지 않나.

나는 그냥 카톡에서 Picky한테 물어보게 만들었다.
7개만 고르면 메뉴 3개 뽑아줌.

카톡에서 Picky 열고 `점심추천` 입력하면 바로 시작.

Use image: `static/promo/kakao-threads-lunch.png`

### 2. Solo Meal

혼밥 메뉴 고르는 게 은근 제일 어렵다.
너무 무겁긴 싫고, 또 너무 대충 먹긴 싫고.

Picky가 상황/맛/먹는 방식 물어보고 메뉴 추천해줌.

카톡에서 `혼밥추천` 입력해봐.

Use image: `static/promo/kakao-story-solo.png`

### 3. Dinner

저녁 메뉴 못 정해서 배달앱만 20분 보는 사람들을 위한 봇 만들었다.

카톡에서 몇 번만 누르면 오늘 먹을 메뉴 후보 3개 나옴.
별로면 다시 추천도 가능.

카톡 Picky에서 `저녁추천`.

### 4. Date Menu

데이트 메뉴는 실패하면 좀 치명적이라 고르기 더 어려움.

Picky가 분위기/맛/형태 기준으로 무난한 후보 뽑아준다.

카톡에서 `데이트메뉴` 입력하면 바로 시작.

### 5. Late Night

야식 먹고 싶은데 치킨/떡볶이/라면에서 매번 멈추는 사람.

Picky한테 `야식추천` 보내면 오늘 상황에 맞춰 3개 추천해줌.

별로면 바로 다른 메뉴도 볼 수 있음.

### 6. Build-in-Public

카톡에서 메뉴 추천해주는 작은 봇을 만들고 있다.

목표는 첫 1,000명.
지금은 피키 캐릭터 카드, 짧은 선택지, 추천 피드백까지 붙였다.

써보고 이상한 점 있으면 알려줘.
카톡에서 `피키추천`.

Use image: `static/promo/kakao-build-log.png`

### 7. Pain Point

오늘 뭐 먹지?

이 질문을 매일 하는데 매번 답이 안 나와서 봇으로 만들었다.
상황 몇 개 고르면 메뉴 3개 추천.

카톡에서 Picky 추가하고 `점심추천`.

### 8. Feedback CTA

Picky 메뉴 추천 봇 테스트해줄 사람 구함.

좋은 점보다 “이거 불편하다”가 더 도움 됨.
특히 선택지가 헷갈리는지, 추천이 납득되는지 보고 싶다.

카톡에서 `피키추천`.

### 9. Before/After

전: 배달앱 켜고 20분 고민

후: 카톡에서 Picky 열고 7번 누른 뒤 후보 3개 받기

오늘 메뉴 결정 줄이고 싶은 사람은 `저녁추천`.

### 10. Weekend

주말에 뭐 먹을지 못 정해서 또 같은 메뉴 먹을 것 같으면
Picky한테 맡겨봐.

혼밥/데이트/야식/국물/매운맛 같은 기준으로 추천해줌.

카톡에서 `피키추천`.

## Short Video Scripts

### Video 1: Lunch in 15 Seconds

Shot list:

1. Screen text: "점심 뭐 먹지?"
2. Show Kakao chat with Picky.
3. Type `점심추천`.
4. Tap 3-4 quick replies quickly.
5. Show result cards.

Voiceover:

"점심 메뉴 고르다 시간 다 쓰는 사람들을 위해 카톡 봇을 만들었습니다. Picky한테 점심추천이라고 보내고 몇 개만 고르면 오늘 먹을 메뉴 후보를 바로 뽑아줘요."

Caption:

카톡에서 Picky 열고 `점심추천`

### Video 2: Solo Meal

Shot list:

1. Desk or laptop scene.
2. Text: "혼밥인데 뭐 먹지?"
3. Open Kakao Picky.
4. Type `혼밥추천`.
5. Show recommendation cards.

Voiceover:

"혼밥 메뉴 고르기 귀찮을 때 카톡에서 Picky한테 혼밥추천이라고 보내보세요. 든든하게 먹을지, 가볍게 먹을지 고르면 후보 3개를 줍니다."

Caption:

혼밥 메뉴 고민 끝. `혼밥추천`

### Video 3: Dinner Scroll Problem

Shot list:

1. Show hand scrolling food delivery app.
2. Text: "20분째 못 고르는 중"
3. Cut to Kakao Picky.
4. Type `저녁추천`.
5. Show final cards and tap "별로" once.

Voiceover:

"배달앱에서 계속 스크롤만 하고 있으면 Picky한테 먼저 물어보세요. 별로인 메뉴는 넘기고 비슷한 메뉴도 볼 수 있게 만들었습니다."

Caption:

저녁 메뉴는 `저녁추천`

### Video 4: Build Log

Shot list:

1. Show Picky character card.
2. Show shortened reply chips.
3. Show food card carousel.
4. Show metrics endpoint blurred except counters.

Voiceover:

"카톡 메뉴 추천 봇 Picky를 1,000명까지 키워보려고 합니다. 이번 업데이트는 캐릭터 카드랑 짧은 선택지입니다. 써보고 피드백 주세요."

Caption:

1,000명 챌린지 시작. `피키추천`

### Video 5: Date Menu

Shot list:

1. Text: "데이트 메뉴 고르기 어려울 때"
2. Type `데이트메뉴`.
3. Select "데이트", "가볍게", "상큼".
4. Show result cards.

Voiceover:

"데이트 메뉴는 너무 무겁지도, 너무 대충도 애매하죠. 카톡에서 Picky한테 데이트메뉴라고 보내면 상황에 맞춰 후보를 골라줍니다."

Caption:

데이트 전엔 `데이트메뉴`

## Daily Execution Checklist

Every day:

1. Publish 1 Threads post using one campaign keyword.
2. Reply to at least 10 relevant "오늘 뭐 먹지" or food-decision posts with a non-spammy suggestion.
3. Record or repost 1 short clip every 2-3 days.
4. Check `/api/kakao/growth`.
5. Write down the best-performing keyword and repeat that angle the next day.

Weekly:

1. Compare `campaignStarts`.
2. If one campaign is at least 2x better than others, create 3 more posts around that use case.
3. If `completionRate` is below 55%, shorten questions or reduce steps.
4. If `feedbackRate` is below 10%, improve result card copy and feedback buttons.

## Measurement Template

| Date | Post keyword | Post URL | Views | Replies | Kakao unique users | Starts | Completions | Completion rate | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2026-__-__ | `점심추천` |  |  |  |  |  |  |  |  |

## Owner Actions Outside Code

These require the app owner account:

1. Add the Kakao channel link to every profile bio used for promotion.
2. Pin one Threads post with the CTA `카톡에서 Picky 열고 피키추천`.
3. Upload 3 short videos in the first week.
4. Apply `docs/kakao-supabase-events.sql` in production Supabase before serious promotion.
5. Check Kakao Open Builder logs after the first 50 users.
