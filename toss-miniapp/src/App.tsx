import { useEffect, useMemo, useState } from "react";

import { fetchQuestions, fetchRecommendations, sendFeedback, trackUsageEvent } from "./api";
import { API_BASE_URL } from "./config";
import { buildReferralShareUrl, getLaunchMetadata } from "./growth";
import { getMenuImageUrl } from "./menuPresentation";
import type { Answers, FeedbackAction, Question, Recommendation, UsageEventName } from "./types";
import "./styles.css";

const mascotImages = {
  loading: "/picky-smile.png",
  question: "/picky-question.png",
  result: "/picky-sausage.png",
  error: "/picky-unsure.png",
};

const optionLabelOverrides: Record<string, string> = {
  "가볍고 깔끔": "깔끔하게",
  "속 따뜻한 국물": "따뜻한 국물",
  "스트레스 풀 매운맛": "매운맛",
  "밥·탄수화물": "밥/탄수",
  "구이·튀김": "구이/튀김",
  "분식·간식": "분식",
  "앉아서 천천히": "천천히",
  "술·야식 같이": "술/야식",
};

function displayOptionLabel(label: string) {
  return optionLabelOverrides[label] ?? label;
}

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

function buildShareText(items: Recommendation[], shareUrl: string) {
  const menuNames = items
    .slice(0, 3)
    .map((item) => item.name)
    .join(", ");

  return `오늘 PICKY 추천 메뉴: ${menuNames}\n토스에서 Picky 메뉴추천으로 골라봤어요.\n${shareUrl}`;
}

function BrandRow() {
  return (
    <div className="brandRow">
      <span className="brandAvatar">
        <img src={mascotImages.result} alt="" />
      </span>
      <span>
        <strong>Picky</strong>
        <small>토스에서 20초 메뉴 결정</small>
      </span>
    </div>
  );
}

export default function App() {
  const [userId] = useState(getAnonymousUserId);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Answers>({});
  const [step, setStep] = useState(0);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "done" | "error">("loading");
  const [message, setMessage] = useState("");
  const launchMetadata = useMemo(() => getLaunchMetadata(window.location.href, document.referrer), []);

  const currentQuestion = questions[step];
  const progressText = useMemo(() => {
    if (!questions.length || recommendations.length) {
      return "";
    }

    return `${Math.min(step + 1, questions.length)} / ${questions.length}`;
  }, [questions.length, recommendations.length, step]);

  useEffect(() => {
    trackEvent(userId, "app_open", launchMetadata);

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
  }, [userId, launchMetadata]);

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
    const shareUrl = buildReferralShareUrl(window.location.href, userId);
    const text = buildShareText(recommendations, shareUrl);

    try {
      if (navigator.share) {
        await navigator.share({
          title: "Picky 메뉴추천",
          text,
          url: shareUrl,
        });
        setMessage("공유를 열었어요.");
      } else {
        await navigator.clipboard.writeText(text);
        setMessage("공유 문구를 복사했어요.");
      }

      trackEvent(userId, "share_clicked", {
        menus: recommendations.map((item) => item.name),
        shareUrl,
      });
    } catch {
      setMessage("공유 문구를 만들지 못했어요.");
    }
  };

  if (status === "loading") {
    return (
      <main className="screen centerScreen">
        <BrandRow />
        <img src={mascotImages.loading} alt="메뉴를 고르는 피키" className="loadingMascot" />
        <h1>메뉴를 고르고 있어요</h1>
        <p className="bodyText">피키가 오늘 분위기에 맞는 후보를 좁히는 중이에요.</p>
      </main>
    );
  }

  if (status === "error") {
    return (
      <main className="screen centerScreen">
        <BrandRow />
        <img src={mascotImages.error} alt="잠시 멈춘 피키" className="loadingMascot" />
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
        <section className="resultHero">
          <div>
            <BrandRow />
            <p className="eyebrow">오늘의 추천</p>
            <h1>피키가 골라왔어요</h1>
            <p className="heroText">마음에 드는 메뉴를 누르면 다음 추천이 더 똑똑해져요.</p>
          </div>
          <img src={mascotImages.result} alt="추천을 들고 온 피키" className="resultMascot" />
        </section>

        <div className="resultToolbar">
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
          {recommendations.map((item) => {
            const imageUrl = getMenuImageUrl(item, API_BASE_URL);

            return (
              <article className="menuCard" key={item.name}>
                <div className="menuBody">
                  <div className="menuSummary">
                    {imageUrl ? (
                      <span className="menuImageFrame">
                        <img src={imageUrl} alt={item.name} className="menuImage" />
                      </span>
                    ) : null}
                    <div className="menuCopy">
                      <p className="category">{item.category}</p>
                      <h2>{item.name}</h2>
                      <p>{item.shortDesc}</p>
                    </div>
                  </div>
                  <div className="tagRow">
                    {item.tags.slice(0, 4).map((tag) => (
                      <span key={tag}>{tag}</span>
                    ))}
                  </div>
                  <div className="actionRow">
                    <button onClick={() => handleFeedback(item.name, "choose")}>결정</button>
                    <button onClick={() => handleFeedback(item.name, "similar")}>비슷한</button>
                    <button onClick={() => handleFeedback(item.name, "dislike")}>별로</button>
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      </main>
    );
  }

  return (
    <main className="screen questionScreen">
      <section className="questionHero">
        <div>
          <BrandRow />
          <p className="eyebrow">질문 {progressText}</p>
          <h1>{currentQuestion?.text ?? "오늘 뭐 먹지?"}</h1>
          <p className="heroText">아래에서 가장 가까운 답 하나만 골라줘요.</p>
        </div>
        <img src={mascotImages.question} alt="질문하는 피키" className="questionMascot" />
      </section>

      {questions.length ? (
        <div className="progressBlock" aria-label={`질문 ${step + 1} / ${questions.length}`}>
          <span>{step + 1}</span>
          <div className="progressTrack">
            <div style={{ width: `${((step + 1) / questions.length) * 100}%` }} />
          </div>
          <span>{questions.length}</span>
        </div>
      ) : null}

      <section className="optionGrid">
        {currentQuestion?.options.map((option) => (
          <button key={option.value} className="optionButton" onClick={() => chooseOption(option.value)}>
            {displayOptionLabel(option.label)}
          </button>
        ))}
      </section>
    </main>
  );
}
