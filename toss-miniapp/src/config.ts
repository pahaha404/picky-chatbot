export const API_BASE_URL =
  import.meta.env.VITE_PICKY_API_BASE_URL?.replace(/\/$/, "") ||
  "https://picky-chatbot-production.up.railway.app";
