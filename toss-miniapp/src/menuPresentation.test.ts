import assert from "node:assert/strict";
import test from "node:test";

import { getMenuImageUrl } from "./menuPresentation.ts";

const apiBaseUrl = "https://picky-chatbot-production.up.railway.app";

test("getMenuImageUrl keeps backend recommendation images first", () => {
  const imageUrl = getMenuImageUrl(
    {
      name: "국밥",
      imageUrl: "/static/foods/generated/gukbap-v2.jpg",
      category: "국밥",
    },
    apiBaseUrl,
  );

  assert.equal(imageUrl, "https://picky-chatbot-production.up.railway.app/static/foods/generated/gukbap-v2.jpg");
});

test("getMenuImageUrl falls back to generated menu images by name", () => {
  const imageUrl = getMenuImageUrl(
    {
      name: "비빔밥",
      imageUrl: null,
      category: "밥",
    },
    apiBaseUrl,
  );

  assert.equal(imageUrl, "/foods/generated/bibimbap.jpg");
});

test("getMenuImageUrl falls back to a category image for uncataloged menu names", () => {
  const imageUrl = getMenuImageUrl(
    {
      name: "부대찌개",
      imageUrl: undefined,
      category: "찌개",
    },
    apiBaseUrl,
  );

  assert.equal(imageUrl, "/foods/generated/kimchi-jjigae-v2.jpg");
});
