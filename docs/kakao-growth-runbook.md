# Kakao Chatbot Growth Runbook

## Current Channel

- Backend: `https://picky-chatbot-production.up.railway.app`
- Kakao Skill endpoint: `/kakao/skill`
- Health check: `/`
- Usage metrics: `/api/kakao/metrics`

## Required Supabase Setup

Run `docs/kakao-supabase-events.sql` in the Supabase SQL Editor before relying on production metrics.
Without this table, the chatbot can still answer, but usage events will not persist after the server restarts.

## 1,000 User Goal

Track the funnel with these events:

- `kakao_start`: user started the recommendation flow
- `kakao_question_answered`: user answered a question
- `kakao_recommendation_completed`: user reached menu recommendations
- `kakao_feedback_clicked`: user clicked choose, similar, or dislike
- `kakao_restart`: user requested another recommendation

Operational targets:

- First 50 users: confirm the chatbot answers correctly and no Kakao Open Builder errors appear.
- 200 users: review completion rate from start to recommendation.
- 500 users: review feedback clicks and improve recommendation text/buttons.
- 1,000 users: compare repeated usage and decide whether to add sharing, coupons, or friend-invite flows.

## Weekly Check

1. Open `/api/kakao/metrics`.
2. Check total users, recommendation completions, feedback clicks, and restarts.
3. If many users start but do not complete seven questions, shorten or reorder questions.
4. If many users complete but do not click feedback, improve card copy and button labels.
5. If repeat usage is low, add a simple reason to come back, such as lunch/dinner presets.
