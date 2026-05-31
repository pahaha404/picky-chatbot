# Kakao Chatbot Growth Runbook

## Current Channel

- Backend: `https://picky-chatbot-production.up.railway.app`
- Kakao Skill endpoint: `/kakao/skill`
- Health check: `/`
- Usage metrics: `/api/kakao/metrics`
- Growth metrics: `/api/kakao/growth`

## Required Supabase Setup

Run `docs/kakao-supabase-events.sql` in the Supabase SQL Editor before relying on production metrics.
Without this table, the chatbot can still answer, but usage events will not persist after the server restarts.

## 1,000 User Goal

Track the funnel with these events:

- `kakao_start`: user started the recommendation flow
- `kakao_question_answered`: user answered a question
- `kakao_recommendation_completed`: user reached menu recommendations
- `kakao_feedback_clicked`: user clicked choose, similar, or dislike
- `kakao_share_prompt`: user requested a copyable friend invite message
- `kakao_restart`: user requested another recommendation

Operational targets:

- First 50 users: confirm the chatbot answers correctly and no Kakao Open Builder errors appear.
- 200 users: review completion rate from start to recommendation.
- 500 users: review feedback clicks and improve recommendation text/buttons.
- 1,000 users: compare repeated usage and decide whether to add sharing, coupons, or friend-invite flows.

Campaign execution:

- Use `docs/kakao-day1-launch-pack.md` for the first 50-user push.
- Use `docs/kakao-1000-growth-campaign.md` for Threads posts, short video scripts, CTA keywords, and the daily checklist.
- Generate the daily execution brief with `.\.venv\Scripts\python.exe scripts\daily_growth_brief.py --note "daily-check"` and post from `docs/kakao-today-growth-brief.md`.
- Use different CTA start messages such as `점심추천`, `저녁추천`, and `혼밥추천` so `/api/kakao/growth` can show which angle brings users.

## Weekly Check

1. Open `/api/kakao/metrics`.
2. Open `/api/kakao/growth`.
   Or run `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_growth_metrics.ps1`.
   To append a dated CSV snapshot, run `.\.venv\Scripts\python.exe scripts\log_growth_snapshot.py --note "weekly-check"`.
   To generate the next posting brief, run `.\.venv\Scripts\python.exe scripts\daily_growth_brief.py --note "weekly-check"`.
3. Check total users, recommendation completions, feedback clicks, share prompts, restarts, and `campaignStarts`.
4. If many users start but do not complete seven questions, shorten or reorder questions.
5. If many users complete but do not click feedback, improve card copy and button labels.
6. If one campaign keyword wins, post 3 more variations of that angle.
