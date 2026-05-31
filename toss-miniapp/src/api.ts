import { API_BASE_URL } from "./config";
import type { Answers, FeedbackAction, Question, Recommendation, UsageEventName } from "./types";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
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
  const body = await requestJson<{ questions: Question[] }>("/api/toss/questions");
  return body.questions;
}

export async function fetchRecommendations(userId: string, answers: Answers): Promise<Recommendation[]> {
  const body = await requestJson<{ recommendations: Recommendation[] }>("/api/toss/recommend", {
    method: "POST",
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
  const body = await requestJson<{ recommendations?: Recommendation[] }>("/api/toss/feedback", {
    method: "POST",
    body: JSON.stringify({ userId, menuName, action, answers }),
  });
  return body.recommendations ?? null;
}

export async function trackUsageEvent(
  userId: string,
  event: UsageEventName,
  metadata: Record<string, unknown> = {},
): Promise<void> {
  await requestJson("/api/toss/events", {
    method: "POST",
    body: JSON.stringify({ userId, event, metadata }),
  });
}
