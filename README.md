# Picky Kakao Chatbot

FastAPI 기반 카카오 챗봇 음식 추천 서버입니다.

## Features

- 카카오 챗봇 Skill endpoint: `/kakao/skill`
- 7단계 취향/상황 질문 플로우
- 음식 카드형 추천 응답
- `이걸로 결정`, `비슷한 메뉴 더 보기`, `별로예요` 피드백 처리
- Supabase 세션/피드백 저장
- 피드백 기반 온라인 보정 및 오프라인 가중치 파일 반영
- Railway 배포 설정 포함

## Local Run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env.local
uvicorn main:app --reload --port 8000
```

## Supabase

Supabase SQL Editor에서 `supabase_schema.sql`을 실행하세요.

필요한 환경변수:

```bash
SUPABASE_URL=...
SUPABASE_KEY=...
PUBLIC_BASE_URL=...
```

## Feedback Weights

피드백 데이터가 충분히 쌓이면 통계 가중치 파일을 생성할 수 있습니다.

```bash
python scripts/build_learned_menu_weights.py
```

## Food Images

기본은 Railway static 이미지 URL을 사용합니다.
Supabase Storage public bucket을 사용할 경우 `food-images` 버킷을 만든 뒤 실행하세요.

```bash
python scripts/upload_food_images.py
```
