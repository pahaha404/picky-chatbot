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

## Kakao Chatbot Operations

카카오 오픈빌더 Skill URL은 Railway 백엔드의 `/kakao/skill`을 사용합니다.
챗봇 시작, 질문 답변, 추천 완료, 피드백, 공유 문구 요청, 다시 추천 이벤트는 서버에서 자동으로 기록되고 `/api/kakao/metrics`에서 집계할 수 있습니다.
Supabase를 쓰는 운영 환경에서는 `docs/kakao-supabase-events.sql`을 SQL Editor에서 실행해 `kakao_usage_events` 테이블을 만들어야 합니다.
운영 지표가 Supabase에 영구 저장되는지 확인하려면 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_storage_health.ps1`를 실행합니다.
카카오 챗봇 1천 명 운영 체크리스트는 `docs/kakao-growth-runbook.md`를 기준으로 진행합니다.
Threads 게시글, 영상 스크립트, 캠페인 시작어, 일일 실행표는 `docs/kakao-1000-growth-campaign.md`에 정리되어 있습니다.
첫 50명 모집용 복붙 게시글, 댓글, 영상 촬영 순서는 `docs/kakao-day1-launch-pack.md`에 정리되어 있습니다.
캠페인별 시작 수와 1천 명 목표 진행률은 `/api/kakao/growth`에서 확인할 수 있습니다.
터미널에서 한 번에 지표를 보려면 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_growth_metrics.ps1`를 실행합니다.
날짜별 지표를 CSV로 남기려면 `.\.venv\Scripts\python.exe scripts\log_growth_snapshot.py --note "daily-check"`를 실행합니다.
오늘 올릴 Threads 게시글, 댓글 10개, 영상 촬영안은 `.\.venv\Scripts\python.exe scripts\daily_growth_brief.py --note "daily-check"`로 `docs/kakao-today-growth-brief.md`에 생성합니다.
홍보 이미지 산출물은 `static/promo/`에 있으며 `scripts/build_kakao_promo_assets.ps1`로 재생성할 수 있습니다.

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

## Toss Miniapp

토스 인앱 MVP는 `toss-miniapp/`에 있으며, 기존 FastAPI 백엔드의 `/api/toss/*` API를 사용합니다.
앱 열림, 질문 로드, 추천 완료, 피드백, 공유, 다시 시작 이벤트는 `/api/toss/events`에 기록되고 `/api/toss/metrics`에서 집계할 수 있습니다.
Supabase를 쓰는 운영 환경에서는 `docs/toss-supabase-events.sql`을 SQL Editor에서 실행해 `toss_usage_events` 테이블을 만들어야 합니다.
운영 지표 저장 상태는 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_storage_health.ps1`로 확인합니다.

배포 구조:

```text
Toss app -> toss-miniapp/picky-menu.ait -> Railway FastAPI backend -> Supabase
```

백엔드:

```bash
uvicorn main:app --reload --port 8000
```

프론트엔드:

```bash
cd toss-miniapp
npm install
npm run dev
```

로컬 개발에서는 `toss-miniapp/.env.development`가 다음 값을 사용합니다.

```bash
VITE_PICKY_API_BASE_URL=http://127.0.0.1:8000
```

배포용 빌드는 별도 값을 지정하지 않으면 Railway 백엔드 `https://picky-chatbot-production.up.railway.app`를 호출합니다.

Apps in Toss QR 테스트 전에는 백엔드 CORS에 토스 도메인을 열어야 합니다.

```bash
TOSS_ALLOWED_ORIGINS=https://picky-menu.apps.tossmini.com,https://picky-menu.private-apps.tossmini.com
```

빌드와 출시 체크리스트:

1. `python -m unittest tests.test_toss_api -v` 실행
2. `cd toss-miniapp && npm run build` 실행
3. 생성된 `picky-menu.ait`를 Apps in Toss 콘솔에 업로드하거나 배포 API 키로 `npx ait deploy --api-key <콘솔_API_키>` 실행
4. 토스앱에서 QR 테스트 완료
5. 앱 내 기능 `메뉴추천` 등록
6. QR 테스트 통과 후 심사 요청

CLI 배포를 반복할 경우 `cd toss-miniapp && npx ait token add`로 콘솔 API 키를 등록한 뒤 `npm run deploy`를 사용할 수 있습니다.

콘솔 업로드, QR 테스트, 심사 요청, 1천 명 지표 운영 절차는 `docs/toss-release-runbook.md`를 기준으로 진행합니다.
