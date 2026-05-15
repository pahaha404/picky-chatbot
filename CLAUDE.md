# CLAUDE.md

This file gives Claude Code the project context needed to work on the Picky Kakao chatbot repository.

## Project Overview

Picky is a FastAPI server for a Kakao chatbot Skill endpoint. It runs a seven-step food preference flow, recommends menu cards, stores sessions and feedback in Supabase when configured, and can adjust recommendations from feedback-derived weights.

Primary endpoint:

- `GET /` health check
- `POST /kakao/skill` Kakao Skill webhook

## Tech Stack

- Python 3.12, pinned for deployment in `runtime.txt`
- FastAPI and Uvicorn
- Supabase Python client
- python-dotenv for local environment loading
- Static food images served from `static/`

Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
uvicorn main:app --reload --port 8000
```

Send the local smoke-test request after the server is running:

```bash
python test_request.py
```

## Repository Map

- `main.py` contains the application, food data, scoring logic, session persistence, feedback learning, Kakao response builders, and API routes.
- `api/index.py` re-exports `app` for platforms that expect an API module entrypoint.
- `supabase_schema.sql` creates `user_sessions` and `menu_feedback`, including RLS policies and feedback indexes.
- `scripts/build_learned_menu_weights.py` builds `learned_menu_weights.json` from Supabase feedback rows.
- `scripts/upload_food_images.py` uploads generated JPG food images to a public Supabase Storage bucket.
- `static/foods/` contains default/category PNG images and generated JPG menu images.
- `README.md` has the short setup guide.
- `railway.json` and `render.yaml` are deployment configs.
- `docs/` may contain partner or planning documents and is not part of the runtime path.

Ignored local/runtime paths include `.env`, `.env.local`, `venv/`, `__pycache__/`, `.tools/`, `*.log`, `ngrok.exe`, and `learned_menu_weights.json`.

## Environment Variables

Use `.env.local` for local secrets. Do not commit real keys.

- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_KEY`: Supabase anon/public key used by this app.
- `PUBLIC_BASE_URL`: public base URL used to build Kakao thumbnail URLs for local static images.
- `LEARNED_MENU_WEIGHTS_PATH`: optional path to a generated weights JSON file. Defaults to `learned_menu_weights.json`.
- `FOOD_IMAGE_BASE_URL`: optional public Supabase Storage URL for generated food images.
- `SUPABASE_FOOD_BUCKET`: storage bucket name used by `scripts/upload_food_images.py`; defaults to `food-images`.

## Runtime Behavior

On import, `main.py` loads `.env` and `.env.local`, creates the FastAPI app, mounts `/static`, initializes Supabase if credentials exist, loads learned menu weights, and enriches food records with public image URLs and tags.

If Supabase is not configured or a Supabase call fails, the app falls back to in-memory dictionaries/lists:

- `USER_SESSIONS`
- `MENU_FEEDBACK`

This keeps local development usable, but production persistence requires Supabase.

## Conversation Flow

The chatbot starts when the normalized utterance matches a start keyword such as `오늘 뭐 먹지`, `메뉴 추천`, `시작`, or `추천`.

The user then answers seven questions:

1. situation
2. meal_goal
3. taste_profile
4. main_ingredient
5. form
6. spice_level
7. eating_style

Answers are stored in the session. When all answers are present, `recommend_food()` returns the top three foods and `build_recommendation_response()` renders them as Kakao `basicCard` carousel items.

Card actions:

- `{menu} 선택` saves `choose` feedback.
- `{menu} 비슷한 메뉴` saves `similar` feedback and calls `recommend_similar_food()`.
- `{menu} 별로예요` saves `dislike` feedback and recommends alternatives.
- `다시 추천` resets the session and restarts the question flow.

## Recommendation Logic

Recommendation scoring combines:

- direct answer-to-food attribute matches via `score_food_attribute_matches()`
- contextual bonuses and penalties via `score_combo_adjustments()`
- online feedback adjustments from recent Supabase or in-memory feedback via `score_feedback_adjustment()`
- optional offline weights from `learned_menu_weights.json` via `score_learned_weight_adjustment()`

The food database is in `FOOD_DB` inside `main.py`. When adding menus, keep fields aligned with the seven question keys and include a concise `short_desc`. Prefer adding an `image_path` under `static/foods/generated/` when a menu has a specific image; otherwise the category fallback image is used.

## Supabase

Run `supabase_schema.sql` in the Supabase SQL editor before using persistence.

Tables:

- `user_sessions`: one row per user, with `step`, `answers`, and `recommendations`.
- `menu_feedback`: feedback events with `user_id`, `menu_name`, `action`, `answers`, and `answer_signature`.

The schema currently allows anon select/insert/update policies because the Kakao webhook uses the configured Supabase key directly from the server. If the API becomes public beyond the Kakao webhook, revisit RLS and key handling.

## Scripts

Build statistical feedback weights:

```bash
python scripts/build_learned_menu_weights.py
```

By default, the script writes only after at least 300 valid feedback rows. Use `--force` only for local testing.

Upload generated food images to Supabase Storage:

```bash
python scripts/upload_food_images.py
```

Before running it, create a public `food-images` bucket or set `SUPABASE_FOOD_BUCKET`.

## Deployment Notes

Railway:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Render uses the same command and checks `GET /`.

For Kakao cards, `thumbnail.imageUrl` must be publicly reachable. Set `PUBLIC_BASE_URL` to the deployed service URL unless `FOOD_IMAGE_BASE_URL` points to Supabase Storage.

## Development Rules

- Keep Kakao responses compatible with version `2.0`.
- Do not commit `.env`, `.env.local`, generated logs, virtualenv files, or real Supabase credentials.
- Avoid changing the shape of `QUESTIONS`, session rows, or feedback rows without updating `supabase_schema.sql` and the scripts.
- Keep `api/index.py` as a simple app re-export unless the deployment target changes.
- When editing recommendation scoring, test both a fresh start utterance and a full seven-answer recommendation path.
- When adding static images, keep paths stable because Kakao card thumbnails depend on public URLs.
