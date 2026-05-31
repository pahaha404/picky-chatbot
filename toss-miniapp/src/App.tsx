import { useEffect, useMemo, useState } from "react";

import { fetchQuestions, fetchRecommendations, sendFeedback, trackUsageEvent } from "./api";
import type { Answers, FeedbackAction, Question, Recommendation, UsageEventName } from "./types";
import "./styles.css";

function createAnonymousUserId() {
  if (crypto.randomUUID) {
    return `toss-${crypto.randomUUID()}`;
  }

  return `toss-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getAnonymousUserId() {
  const storageKey = "picky:toss-user-id";
  const existing = localStorage.getItem(storageKey);

  if (existing) {
    return existing;
  }

  const id = createAnonymousUserId();
  localStorage.setItem(storageKey, id);
  return id;
}

function trackEvent(userId: string, event: UsageEventName, metadata?: Record<string, unknown>) {
  void trackUsageEvent(userId, event, metadata).catch(() => undefined);
}

function buildShareText(items: Recommendation[]) {
  const menuNames = items
    .slice(0, 3)
    .map((item) => item.name)
    .join(", ");

  return `오늘 PICKY 추천 메뉴: ${menuNames}\n토스에서 Picky 메뉴추천으로 골라봤어요.`;
}

export default function App() {
  const [userId] = useState(getAnonymousUserId);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Answers>({});
  const [step, setStep] = useState(0);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "done" | "error">("loading");
  const [message, setMessage] = useState("");

  const currentQuestion = questions[step];
  const progressText = useMemo(() => {
    if (!questions.length || recommendations.length) {
      return "";
    }

    return `${Math.min(step + 1, questions.length)} / ${questions.length}`;
  }, [questions.length, recommendations.length, step]);

  useEffect(() => {
    trackEvent(userId, "app_open");

    fetchQuestions()
      .then((items) => {
        setQuestions(items);
        setStatus("ready");
        trackEvent(userId, "questions_loaded", { total: items.length });
      })
      .catch((error: Error) => {
        setStatus("error");
        setMessage(error.message);
      });
  }, [userId]);

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

    setStatus("loading");

    try {
      const items = await fetchRecommendations(userId, nextAnswers);
      setRecommendations(items);
      setStatus("done");
      trackEvent(userId, "recommendation_completed", { count: items.length });
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "추천을 가져오지 못했어요.");
    }
  };

  const handleFeedback = async (menuName: string, action: FeedbackAction) => {
    setMessage("");

    try {
      const items = await sendFeedback(userId, menuName, action, answers);
      trackEvent(userId, "feedback_clicked", { action, menuName });

      if (items) {
        setRecommendations(items);
      } else {
        setMessage(`${menuName} 좋다. 이걸로 가자.`);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "피드백을 보내지 못했어요.");
    }
  };

  const restart = () => {
    trackEvent(userId, "restart_clicked");
    setAnswers({});
    setStep(0);
    setRecommendations([]);
    setMessage("");
    setStatus(questions.length ? "ready" : "loading");
  };

  const shareRecommendations = async () => {
    const text = buildShareText(recommendations);

    try {
      if (navigator.share) {
        await navigator.share({
          title: "Picky 메뉴추천",
          text,
        });
        setMessage("공유를 열었어요.");
      } else {
        await navigator.clipboard.writeText(text);
        setMessage("공유 문구를 복사했어요.");
      }

      trackEvent(userId, "share_clicked", {
        menus: recommendations.map((item) => item.name),
      });
    } catch {
      setMessage("공유 문구를 만들지 못했어요.");
    }
  };

  if (status === "loading") {
    return (
      <main className="screen">
        <p className="eyebrow">Picky</p>
        <h1>메뉴를 고르고 있어요</h1>
      </main>
    );
  }

  if (status === "error") {
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
          <div className="resultActions">
            <button className="ghostButton" onClick={shareRecommendations}>
              공유
            </button>
            <button className="ghostButton" onClick={restart}>
              다시
            </button>
          </div>
        </div>

        {message ? <p className="notice">{message}</p> : null}

        <section className="recommendationList">
          {recommendations.map((item) => (
            <article className="menuCard" key={item.name}>
              {item.imageUrl ? <img src={item.imageUrl} alt={item.name} className="menuImage" /> : null}
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
                  <button onClick={() => handleFeedback(item.name, "choose")}>결정</button>
                  <button onClick={() => handleFeedback(item.name, "similar")}>비슷한 메뉴</button>
                  <button onClick={() => handleFeedback(item.name, "dislike")}>별로</button>
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
          <h1>{currentQuestion?.text ?? "오늘 뭐 먹지?"}</h1>
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
