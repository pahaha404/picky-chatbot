import assert from "node:assert/strict";
import test from "node:test";

import { buildReferralShareUrl, getLaunchMetadata } from "./growth.ts";

test("buildReferralShareUrl preserves existing query params and adds referral tracking", () => {
  const shareUrl = buildReferralShareUrl("https://picky-menu.apps.tossmini.com/start?entry=food", "toss-user-1");
  const parsed = new URL(shareUrl);

  assert.equal(parsed.origin, "https://picky-menu.apps.tossmini.com");
  assert.equal(parsed.searchParams.get("entry"), "food");
  assert.equal(parsed.searchParams.get("ref"), "toss-user-1");
  assert.equal(parsed.searchParams.get("utm_source"), "share");
  assert.equal(parsed.searchParams.get("utm_medium"), "toss_miniapp");
});

test("getLaunchMetadata extracts referral and UTM fields from the launch URL", () => {
  const metadata = getLaunchMetadata(
    "https://picky-menu.apps.tossmini.com/start?ref=toss-user-1&utm_source=share&utm_medium=toss_miniapp&utm_campaign=first_1000",
    "https://toss.im",
  );

  assert.deepEqual(metadata, {
    referralUserId: "toss-user-1",
    source: "share",
    medium: "toss_miniapp",
    campaign: "first_1000",
    referrer: "https://toss.im",
  });
});

test("getLaunchMetadata marks direct launches when no tracking params exist", () => {
  const metadata = getLaunchMetadata("https://picky-menu.apps.tossmini.com/start", "");

  assert.deepEqual(metadata, {
    source: "direct",
  });
});
