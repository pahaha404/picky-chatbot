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

export type FeedbackAction = "choose" | "similar" | "dislike";
