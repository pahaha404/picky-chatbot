# Toss In-App MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate `toss-miniapp/` Apps in Toss WebView MVP that reuses the existing FastAPI recommendation backend without breaking the Kakao chatbot.

**Architecture:** Keep `main.py` as the backend source of truth for questions, recommendation scoring, sessions, and feedback. Add narrow `/api/toss/*` JSON routes for the Toss frontend, and create a separate `toss-miniapp/` WebView client that calls those routes. The Kakao `/kakao/skill` route remains unchanged and covered by regression tests.

**Tech Stack:** Python 3.12-compatible FastAPI, `unittest` + FastAPI `TestClient`, Apps in Toss WebView toolchain, Vite, React, TypeScript, CSS.

---

## File Structure

- Modify: `main.py`
  - Add CORS middleware for Toss origins and local frontend development.
  - Add Toss request helpers and `/api/toss/*` routes near the existing API route section.
  - Reuse `QUESTIONS`, `VALID_OPTION_VALUES_BY_KEY`, `VALID_FEEDBACK_ACTIONS`, `recommend_food()`, `recommend_similar_food()`, `save_feedback()`, and `save_session()`.
- Create: `tests/test_toss_api.py`
  - Backend API and Kakao regression tests using `unittest`.
- Create: `toss-miniapp/`
  - Apps in Toss WebView app scaffold.
  - Expected files after scaffold/customization: `package.json`, `granite.config.ts`, `index.html`, `src/main.tsx`, `src/App.tsx`, `src/styles.css`, `src/api.ts`, `src/types.ts`, `src/config.ts`.
- Modify: `.env.example`
  - Document `TOSS_ALLOWED_ORIGINS` and `VITE_PICKY_API_BASE_URL`.
- Modify: `README.md`
  - Add local Toss backend/frontend run instructions and Toss build/release checklist.

## Task 1: Backend Toss API Tests

**Files:**
- Create: `tests/test_toss_api.py`

- [ ] **Step 1: Create the backend test file**

Create `tests/test_toss_api.py` with this exact content:

```python
import unittest

from fastapi.testclient import TestClient

from main import ANSWER_KEYS, QUESTIONS, app


VALID_ANSWERS = {
    "situation": "혼밥",
    "meal_goal": "든든한 식사",
    "taste_profile": "매콤",
    "main_ingredient": "고기",
    "form": "밥",
    "spice_level": "매콤",
    "eating_style": "빨리 먹기",
}


class TossApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_questions_returns_public_question_payload(self):
        response = self.client.get("/api/toss/questions")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], len(QUESTIONS))
        self.assertEqual([item["key"] for item in body["questions"]], ANSWER_KEYS)
        self.assertEqual(body["questions"][0]["options"][0]["label"], "혼밥")

    def test_recommend_rejects_missing_answers(self):
        response = self.client.post(
            "/api/toss/recommend",
            json={
                "userId": "test-user",
                "answers": {
                    "situation": "혼밥",
                },
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing answer", response.json()["detail"])

    def test_recommend_rejects_invalid_answer_value(self):
        response = self.client.post(
            "/api/toss/recommend",
            json={
                "userId": "test-user",
                "answers": {
                    **VALID_ANSWERS,
                    "spice_level": "용암맛",
                },
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid answer", response.json()["detail"])

    def test_recommend_returns_three_recommendations(self):
        response = self.client.post(
            "/api/toss/recommend",
            json={
                "userId": "test-user",
                "answers": VALID_ANSWERS,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["userId"], "test-user")
        self.assertEqual(len(body["recommendations"]), 3)
        self.assertIn("name", body["recommendations"][0])
        self.assertIn("shortDesc", body["recommendations"][0])
        self.assertIn("imageUrl", body["recommendations"][0])

    def test_feedback_choose_saves_action(self):
        response = self.client.post(
            "/api/toss/feedback",
            json={
                "userId": "test-user",
                "menuName": "김치찌개",
                "action": "choose",
                "answers": VALID_ANSWERS,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_feedback_similar_returns_recommendations(self):
        response = self.client.post(
            "/api/toss/feedback",
            json={
                "userId": "test-user",
                "menuName": "김치찌개",
                "action": "similar",
                "answers": VALID_ANSWERS,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["recommendations"]), 3)

    def test_feedback_dislike_excludes_menu(self):
        response = self.client.post(
            "/api/toss/feedback",
            json={
                "userId": "test-user",
                "menuName": "김치찌개",
                "action": "dislike",
                "answers": VALID_ANSWERS,
            },
        )

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.json()["recommendations"]]
        self.assertNotIn("김치찌개", names)

    def test_kakao_start_flow_still_works(self):
        response = self.client.post(
            "/kakao/skill",
            json={
                "userRequest": {
                    "utterance": "오늘 뭐 먹지",
                    "user": {
                        "id": "kakao-regression-user",
                    },
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["version"], "2.0")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the failing backend tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_toss_api -v
```

Expected: tests for `/api/toss/questions`, `/api/toss/recommend`, and `/api/toss/feedback` fail with `404 Not Found`; the Kakao regression test passes.

- [ ] **Step 3: Commit the failing tests**

Run:

```powershell
git add tests/test_toss_api.py
git commit -m "test: cover toss API contract"
```

## Task 2: Backend Toss API Implementation

**Files:**
- Modify: `main.py`
- Modify: `.env.example`
- Test: `tests/test_toss_api.py`

- [ ] **Step 1: Add CORS import and configuration**

In `main.py`, add this import after the existing FastAPI import:

```python
from fastapi.middleware.cors import CORSMiddleware
```

Add this environment parsing block after `FOOD_IMAGE_BASE_URL`:

```python
TOSS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "TOSS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,https://picky-menu.apps.tossmini.com,https://picky-menu.private-apps.tossmini.com",
    ).split(",")
    if origin.strip()
]
```

Add this middleware block after `app.mount("/static", StaticFiles(directory="static"), name="static")`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=TOSS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

- [ ] **Step 2: Add Toss payload helpers**

In `main.py`, add this block after `parse_answer()`:

```python
def public_question_payload() -> List[Dict[str, Any]]:
    return [
        {
            "key": question["key"],
            "text": question["text"],
            "options": [
                {
                    "value": value,
                    "label": value,
                }
                for value in question["options"].values()
            ],
        }
        for question in QUESTIONS
    ]


def validate_toss_answers(answers: Dict[str, Any]) -> Dict[str, str]:
    if not isinstance(answers, dict):
        raise ValueError("Answers must be an object.")

    validated: Dict[str, str] = {}

    for key in ANSWER_KEYS:
        if key not in answers:
            raise ValueError(f"Missing answer: {key}")

        value = str(answers[key]).strip()
        if value not in VALID_OPTION_VALUES_BY_KEY[key]:
            raise ValueError(f"Invalid answer for {key}: {value}")

        validated[key] = value

    return validated


def toss_recommendation_payload(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "name": item["name"],
            "score": item.get("score", 0),
            "shortDesc": item.get("short_desc", "지금 먹기 좋은 메뉴야."),
            "imageUrl": item.get("image_url"),
            "category": item.get("category"),
            "tags": item.get("tags", []),
        }
        for item in recommendations
    ]


def normalize_toss_user_id(value: Any) -> str:
    user_id = str(value or "").strip()
    return user_id or "anonymous"
```

- [ ] **Step 3: Add Toss API routes**

In `main.py`, add this block above the existing `@app.post("/kakao/skill")` route:

```python
@app.get("/api/toss/health")
def toss_health_check() -> Dict[str, str]:
    return {
        "status": "ok",
    }


@app.get("/api/toss/questions")
def toss_questions() -> Dict[str, Any]:
    questions = public_question_payload()
    return {
        "total": len(questions),
        "questions": questions,
    }


@app.post("/api/toss/recommend")
async def toss_recommend(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    try:
        answers = validate_toss_answers(payload.get("answers", {}))
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    user_id = normalize_toss_user_id(payload.get("userId"))
    exclude_names = payload.get("excludeNames", [])
    if not isinstance(exclude_names, list):
        exclude_names = []

    recommendations = recommend_food(
        answers,
        exclude_names=[str(name) for name in exclude_names],
    )

    save_session(
        user_id,
        {
            "step": len(QUESTIONS),
            "answers": answers,
            "recommendations": recommendations,
        },
    )

    return JSONResponse(
        content={
            "userId": user_id,
            "recommendations": toss_recommendation_payload(recommendations),
        }
    )


@app.post("/api/toss/feedback")
async def toss_feedback(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    try:
        answers = validate_toss_answers(payload.get("answers", {}))
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    user_id = normalize_toss_user_id(payload.get("userId"))
    menu_name = str(payload.get("menuName", "")).strip()
    action = str(payload.get("action", "")).strip()

    if action not in VALID_FEEDBACK_ACTIONS:
        return JSONResponse(status_code=400, content={"detail": f"Invalid feedback action: {action}"})

    if not menu_name:
        return JSONResponse(status_code=400, content={"detail": "Missing menuName"})

    save_feedback(user_id, menu_name, action, answers)

    response: Dict[str, Any] = {
        "status": "ok",
        "userId": user_id,
        "action": action,
        "menuName": menu_name,
    }

    if action == "similar":
        response["recommendations"] = toss_recommendation_payload(recommend_similar_food(menu_name))

    if action == "dislike":
        response["recommendations"] = toss_recommendation_payload(
            recommend_food(answers, exclude_names=[menu_name])
        )

    return JSONResponse(content=response)
```

- [ ] **Step 4: Document new environment variables**

Append this block to `.env.example`:

```env

# Toss miniapp
TOSS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://picky-menu.apps.tossmini.com,https://picky-menu.private-apps.tossmini.com
VITE_PICKY_API_BASE_URL=http://127.0.0.1:8000
```

- [ ] **Step 5: Run backend tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_toss_api -v
```

Expected: all tests pass.

- [ ] **Step 6: Run a manual API smoke check**

Run:

```powershell
.\.venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; from main import app; c=TestClient(app); print(c.get('/api/toss/health').json()); print(c.get('/api/toss/questions').json()['total'])"
```

Expected output includes:

```text
{'status': 'ok'}
7
```

- [ ] **Step 7: Commit backend API**

Run:

```powershell
git add main.py .env.example tests/test_toss_api.py
git commit -m "feat: add toss recommendation API"
```

## Task 3: Toss WebView Scaffold

**Files:**
- Create: `toss-miniapp/`

- [ ] **Step 1: Scaffold the official WebView app**

Run from the repository root:

```powershell
npx create-ait-app toss-miniapp
```

Prompt selections:

```text
TDS (Toss Design System): Yes
AI Skills: Codex
Example code: No example code
```

Expected: `toss-miniapp/` exists and includes `package.json` and `granite.config.ts`.

- [ ] **Step 2: Install frontend dependencies**

Run:

```powershell
cd toss-miniapp
npm install
cd ..
```

Expected: `toss-miniapp/node_modules/` is installed locally and `package-lock.json` exists or is updated.

- [ ] **Step 3: Set Apps in Toss config**

Replace `toss-miniapp/granite.config.ts` with this content:

```ts
import { defineConfig } from '@apps-in-toss/web-framework/config';

export default defineConfig({
  appName: 'picky-menu',
  brand: {
    displayName: 'Picky 메뉴추천',
    primaryColor: '#3182F6',
    icon: '',
  },
  web: {
    host: 'localhost',
    port: 5173,
    commands: {
      dev: 'vite dev',
      build: 'vite build',
    },
  },
  permissions: [],
  outdir: 'dist',
});
```

- [ ] **Step 4: Commit scaffold**

Run:

```powershell
git add toss-miniapp
git commit -m "chore: scaffold toss miniapp"
```

## Task 4: Toss Frontend Implementation

**Files:**
- Create: `toss-miniapp/src/types.ts`
- Create: `toss-miniapp/src/config.ts`
- Create: `toss-miniapp/src/api.ts`
- Modify: `toss-miniapp/src/App.tsx`
- Modify: `toss-miniapp/src/styles.css`

- [ ] **Step 1: Create shared frontend types**

Create `toss-miniapp/src/types.ts`:

```ts
export type Question = {
  key: string;
  text: string;
  options: Array<{
    value: string;
    label: string;
  }>;
};

export type Recommendation = {
  name: string;
  score: number;
  shortDesc: string;
  imageUrl?: string | null;
  category?: string | null;
  tags: string[];
};

export type Answers = Record<string, string>;

export type FeedbackAction = 'choose' | 'similar' | 'dislike';
```

- [ ] **Step 2: Create API base config**

Create `toss-miniapp/src/config.ts`:

```ts
export const API_BASE_URL =
  import.meta.env.VITE_PICKY_API_BASE_URL?.replace(/\/$/, '') || 'http://127.0.0.1:8000';
```

- [ ] **Step 3: Create API client**

Create `toss-miniapp/src/api.ts`:

```ts
import { API_BASE_URL } from './config';
import type { Answers, FeedbackAction, Question, Recommendation } from './types';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function fetchQuestions(): Promise<Question[]> {
  const body = await requestJson<{ questions: Question[] }>('/api/toss/questions');
  return body.questions;
}

export async function fetchRecommendations(userId: string, answers: Answers): Promise<Recommendation[]> {
  const body = await requestJson<{ recommendations: Recommendation[] }>('/api/toss/recommend', {
    method: 'POST',
    body: JSON.stringify({ userId, answers }),
  });
  return body.recommendations;
}

export async function sendFeedback(
  userId: string,
  menuName: string,
  action: FeedbackAction,
  answers: Answers,
): Promise<Recommendation[] | null> {
  const body = await requestJson<{ recommendations?: Recommendation[] }>('/api/toss/feedback', {
    method: 'POST',
    body: JSON.stringify({ userId, menuName, action, answers }),
  });
  return body.recommendations ?? null;
}
```

- [ ] **Step 4: Replace app UI**

Replace `toss-miniapp/src/App.tsx` with this content. If the scaffold uses `src/main.tsx` to render another component, update that import to use `App` from this file.

```tsx
import { useEffect, useMemo, useState } from 'react';
import { fetchQuestions, fetchRecommendations, sendFeedback } from './api';
import type { Answers, FeedbackAction, Question, Recommendation } from './types';
import './styles.css';

function getAnonymousUserId() {
  const storageKey = 'picky:toss-user-id';
  const existing = localStorage.getItem(storageKey);

  if (existing) {
    return existing;
  }

  const id = `toss-${crypto.randomUUID()}`;
  localStorage.setItem(storageKey, id);
  return id;
}

export default function App() {
  const [userId] = useState(getAnonymousUserId);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Answers>({});
  const [step, setStep] = useState(0);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'done' | 'error'>('loading');
  const [message, setMessage] = useState('');

  const currentQuestion = questions[step];
  const progressText = useMemo(() => {
    if (!questions.length || recommendations.length) {
      return '';
    }

    return `${Math.min(step + 1, questions.length)} / ${questions.length}`;
  }, [questions.length, recommendations.length, step]);

  useEffect(() => {
    fetchQuestions()
      .then((items) => {
        setQuestions(items);
        setStatus('ready');
      })
      .catch((error: Error) => {
        setStatus('error');
        setMessage(error.message);
      });
  }, []);

  const chooseOption = async (value: string) => {
    if (!currentQuestion) {
      return;
    }

    const nextAnswers = {
      ...answers,
      [currentQuestion.key]: value,
    };

    setAnswers(nextAnswers);

    if (step + 1 < questions.length) {
      setStep(step + 1);
      return;
    }

    setStatus('loading');

    try {
      const items = await fetchRecommendations(userId, nextAnswers);
      setRecommendations(items);
      setStatus('done');
    } catch (error) {
      setStatus('error');
      setMessage(error instanceof Error ? error.message : '추천을 가져오지 못했어요.');
    }
  };

  const handleFeedback = async (menuName: string, action: FeedbackAction) => {
    setMessage('');

    try {
      const items = await sendFeedback(userId, menuName, action, answers);

      if (items) {
        setRecommendations(items);
      } else {
        setMessage(`${menuName} 좋다. 이걸로 가자.`);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '피드백을 보내지 못했어요.');
    }
  };

  const restart = () => {
    setAnswers({});
    setStep(0);
    setRecommendations([]);
    setMessage('');
    setStatus(questions.length ? 'ready' : 'loading');
  };

  if (status === 'loading') {
    return (
      <main className="screen">
        <p className="eyebrow">Picky</p>
        <h1>메뉴를 고르고 있어요</h1>
      </main>
    );
  }

  if (status === 'error') {
    return (
      <main className="screen">
        <p className="eyebrow">Picky</p>
        <h1>잠시 후 다시 시도해 주세요</h1>
        <p className="bodyText">{message}</p>
        <button className="primaryButton" onClick={() => window.location.reload()}>
          다시 시도
        </button>
      </main>
    );
  }

  if (recommendations.length) {
    return (
      <main className="screen resultsScreen">
        <div className="topBar">
          <div>
            <p className="eyebrow">오늘의 추천</p>
            <h1>이 중에서 골라볼까요?</h1>
          </div>
          <button className="ghostButton" onClick={restart}>
            다시
          </button>
        </div>

        {message ? <p className="notice">{message}</p> : null}

        <section className="recommendationList">
          {recommendations.map((item) => (
            <article className="menuCard" key={item.name}>
              {item.imageUrl ? <img src={item.imageUrl} alt="" className="menuImage" /> : null}
              <div className="menuBody">
                <p className="category">{item.category}</p>
                <h2>{item.name}</h2>
                <p>{item.shortDesc}</p>
                <div className="tagRow">
                  {item.tags.slice(0, 4).map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
                <div className="actionRow">
                  <button onClick={() => handleFeedback(item.name, 'choose')}>결정</button>
                  <button onClick={() => handleFeedback(item.name, 'similar')}>비슷한 메뉴</button>
                  <button onClick={() => handleFeedback(item.name, 'dislike')}>별로</button>
                </div>
              </div>
            </article>
          ))}
        </section>
      </main>
    );
  }

  return (
    <main className="screen">
      <div className="topBar">
        <div>
          <p className="eyebrow">Picky 메뉴추천</p>
          <h1>{currentQuestion?.text ?? '오늘 뭐 먹지?'}</h1>
        </div>
        {progressText ? <span className="progress">{progressText}</span> : null}
      </div>

      <section className="optionGrid">
        {currentQuestion?.options.map((option) => (
          <button key={option.value} className="optionButton" onClick={() => chooseOption(option.value)}>
            {option.label}
          </button>
        ))}
      </section>
    </main>
  );
}
```

- [ ] **Step 5: Replace styles**

Replace `toss-miniapp/src/styles.css` with this content:

```css
:root {
  color: #1f2933;
  background: #f6f8fb;
  font-family:
    Inter,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  background: #f6f8fb;
}

button {
  border: 0;
  font: inherit;
}

.screen {
  min-height: 100vh;
  padding: 24px 18px 32px;
}

.topBar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.eyebrow,
.category {
  margin: 0 0 8px;
  color: #3182f6;
  font-size: 13px;
  font-weight: 700;
}

h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.22;
  letter-spacing: 0;
}

h2 {
  margin: 2px 0 8px;
  font-size: 22px;
  line-height: 1.25;
  letter-spacing: 0;
}

.bodyText,
.menuBody p {
  color: #536471;
  line-height: 1.5;
}

.progress {
  min-width: 52px;
  padding: 8px 10px;
  border-radius: 999px;
  background: #e8f2ff;
  color: #1f6feb;
  font-size: 13px;
  font-weight: 700;
  text-align: center;
}

.optionGrid {
  display: grid;
  gap: 12px;
}

.optionButton,
.primaryButton,
.ghostButton {
  min-height: 52px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 800;
}

.optionButton {
  width: 100%;
  padding: 16px;
  background: #ffffff;
  color: #1f2933;
  text-align: left;
  box-shadow: 0 1px 8px rgba(15, 23, 42, 0.08);
}

.primaryButton {
  margin-top: 18px;
  padding: 0 18px;
  background: #3182f6;
  color: #ffffff;
}

.ghostButton {
  min-height: 42px;
  padding: 0 14px;
  background: #ffffff;
  color: #3182f6;
}

.notice {
  margin: 0 0 14px;
  padding: 12px 14px;
  border-radius: 8px;
  background: #e8f2ff;
  color: #1f4f8f;
  font-weight: 700;
}

.recommendationList {
  display: grid;
  gap: 14px;
}

.menuCard {
  overflow: hidden;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 10px rgba(15, 23, 42, 0.1);
}

.menuImage {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  background: #dbe4ee;
}

.menuBody {
  padding: 16px;
}

.tagRow {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 12px 0 14px;
}

.tagRow span {
  padding: 5px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #52616f;
  font-size: 12px;
  font-weight: 700;
}

.actionRow {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.actionRow button {
  min-height: 42px;
  border-radius: 8px;
  background: #f6f8fb;
  color: #26323f;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

@media (min-width: 720px) {
  .screen {
    max-width: 720px;
    margin: 0 auto;
  }
}
```

- [ ] **Step 6: Run frontend type/build verification**

Run:

```powershell
cd toss-miniapp
npm run build
cd ..
```

Expected: build succeeds and creates an Apps in Toss `.ait` bundle or the configured build output required by the installed Apps in Toss toolchain.

- [ ] **Step 7: Commit frontend implementation**

Run:

```powershell
git add toss-miniapp
git commit -m "feat: build toss miniapp flow"
```

## Task 5: Documentation And Release Checklist

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Toss local run instructions**

Append this section to `README.md`:

````markdown

## Toss Miniapp

The Toss in-app MVP lives in `toss-miniapp/` and reuses this FastAPI backend through `/api/toss/*`.

Backend:

```bash
uvicorn main:app --reload --port 8000
```

Frontend:

```bash
cd toss-miniapp
npm install
npm run dev
```

Set `VITE_PICKY_API_BASE_URL=http://127.0.0.1:8000` for local development.

Before Apps in Toss QR testing, set backend CORS through `TOSS_ALLOWED_ORIGINS`:

```bash
TOSS_ALLOWED_ORIGINS=https://picky-menu.apps.tossmini.com,https://picky-menu.private-apps.tossmini.com
```

Build and release checklist:

1. Run `python -m unittest tests.test_toss_api -v`.
2. Run `cd toss-miniapp && npm run build`.
3. Upload the generated `.ait` bundle in the Apps in Toss console or use `npx ait deploy`.
4. Complete at least one QR test in the Toss app.
5. Register the in-app function `메뉴추천`.
6. Request review after QR testing passes.
````

- [ ] **Step 2: Run final backend regression tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_toss_api -v
```

Expected: all tests pass.

- [ ] **Step 3: Run final frontend build**

Run:

```powershell
cd toss-miniapp
npm run build
cd ..
```

Expected: build succeeds.

- [ ] **Step 4: Check Git state**

Run:

```powershell
git status --short
```

Expected: only intentional README changes are unstaged before the commit.

- [ ] **Step 5: Commit docs**

Run:

```powershell
git add README.md
git commit -m "docs: add toss miniapp release checklist"
```

## Task 6: Local End-To-End Verification

**Files:**
- No source files expected unless verification finds a defect.

- [ ] **Step 1: Start the backend**

Run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Expected: FastAPI starts on `http://127.0.0.1:8000`.

- [ ] **Step 2: Start the frontend**

In a second terminal, run:

```powershell
cd toss-miniapp
npm run dev
```

Expected: frontend starts on `http://localhost:5173`.

- [ ] **Step 3: Use Browser verification**

Open `http://localhost:5173`, complete all seven questions, and verify:

- The first screen is the actual recommendation flow.
- No visible text overlaps on mobile width.
- Three recommendation cards render.
- "결정" shows a confirmation notice.
- "비슷한 메뉴" replaces recommendations.
- "별로" replaces recommendations without the disliked menu.

- [ ] **Step 4: Commit any verification fixes**

If verification requires fixes, commit them with a focused message:

```powershell
git add main.py toss-miniapp README.md tests/test_toss_api.py
git commit -m "fix: polish toss miniapp verification"
```

## Self-Review

- Spec coverage: The plan covers separate `toss-miniapp/`, backend reuse, `/api/toss/*` APIs, anonymous MVP, feedback actions, CORS, build, QR-test checklist, and Kakao regression.
- Empty-section scan: The plan avoids empty sections and unspecified implementation steps. The app name is fixed as `picky-menu`.
- Type consistency: Backend response fields use `shortDesc` and `imageUrl`; frontend `Recommendation` uses the same names.
- Scope control: Toss Login, official user identity, smart messages, and growth campaigns are excluded from MVP implementation and reserved for post-launch work.
