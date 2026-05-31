# Toss In-App Picky Design

## Goal

Build a Toss in-app version of Picky without disrupting the existing Kakao chatbot. The first release should let an anonymous Toss user answer the same seven food-preference questions, receive three menu recommendations, send simple feedback, pass Toss QR testing, and be ready for Apps in Toss review.

The broader success target is to launch the miniapp and acquire 1,000 users. This design covers the product and technical foundation needed to ship the first Toss MVP; distribution work continues after the MVP can be tested in Toss.

## Current Project Context

The repository is currently a FastAPI Kakao chatbot server. `main.py` owns the app, the seven-question flow, the food database, recommendation scoring, session persistence, feedback persistence, Kakao response builders, and the `/kakao/skill` route. `api/index.py` re-exports the FastAPI app for deployment targets. Static food images are served from `/static`.

Baseline verification on this branch passed after installing `requirements.txt` into a local virtual environment:

- `from main import app` imports successfully.
- `GET /` returns `200`.
- `POST /kakao/skill` with the start utterance returns `200` and Kakao response version `2.0`.

## Chosen Approach

Create a separate `toss-miniapp/` folder for the Apps in Toss WebView app and reuse the existing FastAPI backend for recommendation logic. The Kakao chatbot remains available at `/kakao/skill`; Toss uses new `/api/toss/*` JSON endpoints.

This keeps the Kakao surface stable, gives Toss its own frontend and build settings, and avoids copying the recommendation engine into a second service.

## Architecture

```text
picky_chatbot/
  main.py
    existing Kakao chatbot route
    existing recommendation/session/feedback logic
    new Toss JSON API routes
  api/index.py
    existing app re-export
  static/
    existing food images
  toss-miniapp/
    Apps in Toss WebView frontend
    build output packaged as .ait
  docs/superpowers/
    design and implementation plans
```

The backend remains the source of truth for questions, menu scoring, image URLs, and feedback learning. The Toss frontend is a thin client that renders the question flow and calls JSON APIs.

## Backend API Design

Add a small Toss API layer to `main.py`. The API should reuse existing functions instead of duplicating scoring or food data.

`GET /api/toss/health`

- Returns `{ "status": "ok" }`.
- Used by the frontend and deployment checks.

`GET /api/toss/questions`

- Returns the seven existing questions with stable keys, Korean prompt text, and option labels.
- Does not expose Kakao response JSON.

`POST /api/toss/recommend`

- Request body:

```json
{
  "userId": "anonymous-or-client-generated-id",
  "answers": {
    "situation": "혼밥",
    "meal_goal": "든든한 식사",
    "taste_profile": "매콤",
    "main_ingredient": "고기",
    "form": "밥",
    "spice_level": "매콤",
    "eating_style": "빨리 먹기"
  },
  "excludeNames": []
}
```

- Validates that all seven answer keys exist and use known option labels.
- Calls `recommend_food(answers, exclude_names=excludeNames)`.
- Saves the latest anonymous session when persistence is available.
- Returns recommendations as plain JSON with name, description, image URL, category, tags, and score.

`POST /api/toss/feedback`

- Request body:

```json
{
  "userId": "anonymous-or-client-generated-id",
  "menuName": "김치찌개",
  "action": "choose",
  "answers": {
    "situation": "혼밥",
    "meal_goal": "든든한 식사",
    "taste_profile": "매콤",
    "main_ingredient": "고기",
    "form": "밥",
    "spice_level": "매콤",
    "eating_style": "빨리 먹기"
  }
}
```

- Allows the existing feedback actions: `choose`, `similar`, `dislike`.
- Calls `save_feedback()`.
- For `similar`, returns `recommend_similar_food(menuName)`.
- For `dislike`, returns a fresh `recommend_food()` result excluding that menu when answers are present.

## Toss Miniapp UX

The Toss MVP is loginless and anonymous. The frontend generates or stores a local anonymous ID and sends it with requests. Toss Login and official user identity can be added after the first release if retention or personalization requires it.

Primary flow:

1. Landing state with a direct "오늘 뭐 먹지?" start action.
2. Seven single-choice question screens using the existing backend question order.
3. Recommendation screen showing three menu cards with image, name, short description, and tags.
4. Feedback actions per recommendation: "이걸로 결정", "비슷한 메뉴", "별로예요".
5. Restart action to clear local answers and start again.

The first screen should be the usable product, not a marketing page. The UI should be compact, touch-friendly, and optimized for mobile WebView.

## Toss Platform Requirements

Apps in Toss currently supports WebView and React Native starts. The WebView path is the fastest fit for this project. The implementation should be scaffolded under `toss-miniapp/` with the official Apps in Toss toolchain, build to an `.ait` bundle, and be uploaded through the Apps in Toss console or `npx ait deploy`.

Deployment checks:

- Build creates an `.ait` bundle.
- Bundle stays below the Apps in Toss bundle size limit.
- QR test is completed in the Toss app before review request.
- Backend CORS allows both Toss origins for the working app name `picky-menu`:
  - `https://picky-menu.apps.tossmini.com`
  - `https://picky-menu.private-apps.tossmini.com`
- Production API calls use HTTPS.
- At least one in-app function is registered in the Apps in Toss console. Recommended function name: `메뉴추천`.

## Analytics And 1,000-User Growth

The MVP should capture lightweight usage events through the backend or existing Supabase setup:

- Anonymous user ID creation.
- Recommendation completed.
- Feedback action clicked.
- Restart clicked.

For the first 1,000 users, the product loop should be:

- Make the recommendation result easy to screenshot or share.
- Use the Toss app listing and function entry point as the main acquisition surface.
- Use recommendation completion rate and feedback click rate as the first quality metrics.
- Add Toss Login only when it clearly improves retention, personalization, or messaging.

## Error Handling

Backend validation errors should return clear `400` JSON responses with a short message. Frontend network failures should show a retry action without losing local answers. If image URLs fail, recommendation cards should still render text.

Supabase remains optional. If Supabase credentials are missing or a write fails, the backend should continue using the existing in-memory fallback so local and QR testing are not blocked.

## Testing Plan

Backend tests should cover:

- `GET /api/toss/questions` returns seven questions.
- `POST /api/toss/recommend` rejects missing or invalid answers.
- `POST /api/toss/recommend` returns three recommendations for valid answers.
- `POST /api/toss/feedback` accepts `choose`, `similar`, and `dislike`.
- Existing `/kakao/skill` start flow still returns Kakao version `2.0`.

Frontend verification should cover:

- The miniapp renders on a mobile viewport.
- The user can complete all seven questions without typing.
- Recommendation cards render image, title, description, and actions.
- Feedback actions call the backend and update the screen.
- The production build succeeds and produces an `.ait` bundle.

## Risks

The main technical risk is that `main.py` is already large. The first implementation should add only a narrow Toss API layer. Any larger refactor should be limited to extracting reusable validation or response helpers when it directly reduces duplication.

The main launch risk is platform approval. The build and QR-test path should be verified early with the official Apps in Toss toolchain before investing in advanced personalization.

The main growth risk is weak differentiation from generic menu recommendation. The MVP should emphasize fast completion, visually clear results, and feedback learning before adding heavier features.
