# Toss Miniapp Release Runbook

Last updated: 2026-05-31

This runbook tracks the remaining steps to release the Picky Toss miniapp and start measuring the first 1,000 users.

## Current Build

- App folder: `toss-miniapp/`
- Git branch: `codex/toss-inapp`
- App ID: `picky-menu`
- Display name: `Picky 메뉴추천`
- Backend: `https://picky-chatbot-production.up.railway.app`
- Build artifact: `toss-miniapp/picky-menu.ait`
- Artifact size at last local check: about 4.5 MB
- Latest release check: 2026-05-31 21:17 KST
- Latest local checks passed:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_toss_api -v` with 16 tests passing
  - `npm run lint`
  - `npm run test:growth`
  - `npm run build`
- Production API smoke checks verified:
  - `GET /api/toss/health`
  - `GET /api/toss/questions`
  - `POST /api/toss/recommend`
  - `POST /api/toss/events`
  - `GET /api/toss/metrics`
- Production CORS verified:
  - `https://picky-menu.apps.tossmini.com`
  - `https://picky-menu.private-apps.tossmini.com`
- Apps in Toss CLI deploy reached the API-key prompt:
  - `npx ait deploy --location ./picky-menu.ait --scheme-only -m "..."`
  - Result: blocked until a console deploy API key is entered or the `.ait` file is uploaded manually.

## Hosting Architecture

Apps in Toss hosts and runs the miniapp bundle, not this project's FastAPI backend.

```text
Toss app
  -> Apps in Toss WebView bundle: toss-miniapp/picky-menu.ait
  -> Railway backend: https://picky-chatbot-production.up.railway.app
  -> Supabase Postgres: sessions, feedback, usage events
```

Current hosting split:

- Toss console upload: only the frontend `.ait` bundle.
- Railway: the existing FastAPI server used by both Kakao and Toss.
- Supabase: persistent database storage.

Do not create a second backend for the first release unless Railway becomes unreliable. The fastest launch path is to keep using Railway and verify CORS from the Toss private and public origins.

## Hard Blockers

These require the app owner in external consoles.

1. Apps in Toss console access.
2. Apps in Toss deploy API key, or manual `.ait` upload in the console.
3. Supabase SQL Editor access to apply `docs/toss-supabase-events.sql` in production, otherwise usage metrics can fall back to memory and reset after backend restarts.
4. Toss app on a real phone for QR testing.
5. Review request in the Apps in Toss console after QR testing passes.

## Official Release Requirements Checked

Sources:

- Apps in Toss developer center: https://developers-apps-in-toss.toss.im/
- WebView guide: https://developers-apps-in-toss.toss.im/tutorials/webview.html
- Common config guide: https://developers-apps-in-toss.toss.im/bedrock/reference/framework/UI/Config.html
- Toss app testing guide: https://developers-apps-in-toss.toss.im/development/test/toss.html
- Miniapp release guide: https://developers-apps-in-toss.toss.im/development/deploy.html
- Non-game checklist: https://developers-apps-in-toss.toss.im/checklist/app-nongame.html
- Growth guide index: https://developers-apps-in-toss.toss.im/llms.txt

Relevant requirements for this app:

- WebView miniapps use `create-ait-app` or `@apps-in-toss/web-framework`; this project uses the official WebView toolchain.
- `appName`, `displayName`, and `icon` in `granite.config.ts` must match console app information. `icon` currently uses the bundled Picky mascot asset at `/picky-sausage.png`; replace it with a console-hosted logo URL only if the Apps in Toss console rejects local bundled assets.
- Non-game miniapps should use the partner navigation frame; `webViewProps.type` is set to `partner`.
- The app bundle must be below the Apps in Toss bundle size limit. The current `.ait` artifact is well below 100 MB.
- QR testing in the Toss app must be completed at least once before review can be requested.
- Review can take up to 3 business days.
- Backend CORS must allow both service origins:
  - `https://picky-menu.apps.tossmini.com`
  - `https://picky-menu.private-apps.tossmini.com`

## Console Registration Values

Use these values unless the app name changes in the console.

- Korean app name: `Picky 메뉴추천`
- English app name: `Picky Menu`
- App ID / appName: `picky-menu`
- Type: Non-game
- Suggested category: lifestyle, food, utility, or closest available non-game category
- Suggested keywords:
  - `메뉴추천`
  - `점심추천`
  - `저녁추천`
  - `오늘뭐먹지`
  - `음식추천`
  - `혼밥`
  - `데이트`
  - `야식`
  - `Picky`
  - `피키`
- Customer support email/contact: app owner must provide this.
- Homepage URL: optional; use GitHub or a simple service intro page if required.
- Logo: use `toss-miniapp/public/picky-sausage.png` as the first console logo candidate.

## Pre-Upload Checklist

Run from the repo root:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_toss_api -v
```

Run from `toss-miniapp/`:

```powershell
npm run lint
npm run build
```

Expected output:

- Backend: 16 tests pass.
- Frontend lint: no errors.
- Build: `picky-menu.ait` is created.

Before upload, check:

- `toss-miniapp/granite.config.ts` `brand.icon` is not empty.
- `PUBLIC_BASE_URL` on Railway is `https://picky-chatbot-production.up.railway.app`.
- `TOSS_ALLOWED_ORIGINS` includes both public and private Toss origins.
- Production Supabase has the `toss_usage_events` table.

## Production Supabase Setup

The Toss miniapp works without this table, but usage metrics reset whenever the Railway process restarts. Apply the SQL before QR testing if you want reliable first-1,000-user tracking.

1. Open Supabase dashboard.
2. Open the production project used by Railway `SUPABASE_URL` and `SUPABASE_KEY`.
3. Go to SQL Editor.
4. Paste and run `docs/toss-supabase-events.sql`.
5. Open `Table Editor` and confirm `toss_usage_events` exists.
6. Run a public API smoke event:

```powershell
curl.exe -sS -X POST https://picky-chatbot-production.up.railway.app/api/toss/events -H "Content-Type: application/json" --data-binary "{\"userId\":\"supabase-check\",\"event\":\"app_open\"}"
```

7. Confirm the event appears in Supabase or in:

```text
https://picky-chatbot-production.up.railway.app/api/toss/metrics
```

Security notes:

- RLS is enabled for `toss_usage_events`.
- The SQL grants only `select` and `insert` to `anon`, because the backend only needs to write events and read them for metrics.
- Do not put the Supabase `service_role` key in the Toss miniapp frontend.

## Upload Options

Manual console upload:

1. Open https://apps-in-toss.toss.im/
2. Select workspace.
3. Select or create the `picky-menu` miniapp.
4. Upload `toss-miniapp/picky-menu.ait`.
5. Create a QR test build.

CLI deploy:

```powershell
cd toss-miniapp
npx ait token add --api-key <CONSOLE_API_KEY> default
npm run build
npx ait deploy --profile default -m "Picky Toss miniapp MVP: questions, recommendations, feedback, sharing, usage metrics"
```

One-off CLI deploy without storing the token:

```powershell
cd toss-miniapp
npm run build
npx ait deploy --api-key <CONSOLE_API_KEY> --location ./picky-menu.ait -m "Picky Toss miniapp MVP"
```

## QR Test Script

Use the QR code from the Apps in Toss console and test on a real Toss app.

1. Open QR code in Toss.
2. Confirm the first screen is the actual question flow, not a landing page.
3. Answer all 7 questions.
4. Confirm 3 recommendation cards render.
5. Tap `결정` and confirm the notice appears.
6. Tap `비슷한 메뉴` and confirm recommendations refresh.
7. Tap `별로` and confirm recommendations refresh without the disliked menu.
8. Tap `공유` and confirm Toss/native share or copy behavior works.
9. Tap `다시` and confirm the flow resets.
10. Open:

```text
https://picky-chatbot-production.up.railway.app/api/toss/metrics
```

Confirm the following counters moved:

- `app_open`
- `questions_loaded`
- `recommendation_completed`
- `feedback_clicked`
- `share_clicked`
- `restart_clicked`

## Review Request Checklist

Request review only after QR testing passes.

1. Confirm app information review is complete.
2. Confirm QR test is complete at least once.
3. Confirm production CORS works from the private Toss origin.
4. Confirm the app opens within 10 seconds on mobile data.
5. Confirm no external app-install prompt or unrelated external link exists.
6. Confirm the app uses the non-game navigation frame.
7. Confirm all text is appropriate for a general audience.
8. Confirm no login, payment, ads, location, camera, or sensitive permissions are used.
9. Click `검토 요청하기` in the Apps in Toss console.

## First 1,000 Users Plan

Track progress through `/api/toss/metrics`.
The app also writes launch-source metadata on `app_open`.
When a user opens a shared link, the event metadata includes `referralUserId`, `source=share`, and `medium=toss_miniapp`.
The share button appends `ref`, `utm_source=share`, and `utm_medium=toss_miniapp` to the shared URL.

Milestone 1: first 50 QR/test users

- Goal: verify no launch-blocking bugs before public release.
- Watch: `recommendation_completed / app_open`.
- Action threshold: if completion rate is below 60%, shorten copy or improve question flow.

Milestone 2: first 200 public users

- Goal: confirm the app listing and app function entry point bring qualified users.
- Watch: `feedback_clicked / recommendation_completed` and `share_clicked / recommendation_completed`.
- Action threshold: if share rate is below 5%, change result copy or make the share button more prominent.

Milestone 3: first 1,000 users

- Goal: stabilize an acquisition loop.
- Primary loops:
  - App function: `메뉴추천`
  - Search keywords: menu, lunch, dinner, food recommendation terms
  - Result sharing: users share their top 3 menu recommendations
- Watch:
  - unique users
  - completion rate
  - feedback rate
  - share rate
  - referred app opens from shared links
  - repeat `app_open` after previous completion

Do not add Toss Login, notifications, ads, or rewards before the QR/review path is accepted unless the review process requires them.
