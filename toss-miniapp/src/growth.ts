export type LaunchMetadata = Record<string, string>;

function trackedValue(searchParams: URLSearchParams, key: string) {
  return searchParams.get(key)?.trim() || "";
}

export function buildReferralShareUrl(currentHref: string, userId: string) {
  const url = new URL(currentHref);

  url.searchParams.set("ref", userId);
  url.searchParams.set("utm_source", "share");
  url.searchParams.set("utm_medium", "toss_miniapp");

  return url.toString();
}

export function getLaunchMetadata(currentHref: string, referrer = ""): LaunchMetadata {
  const url = new URL(currentHref);
  const metadata: LaunchMetadata = {};
  const referralUserId = trackedValue(url.searchParams, "ref");
  const source = trackedValue(url.searchParams, "utm_source");
  const medium = trackedValue(url.searchParams, "utm_medium");
  const campaign = trackedValue(url.searchParams, "utm_campaign");
  const cleanReferrer = referrer.trim();

  if (referralUserId) {
    metadata.referralUserId = referralUserId;
  }

  metadata.source = source || "direct";

  if (medium) {
    metadata.medium = medium;
  }

  if (campaign) {
    metadata.campaign = campaign;
  }

  if (cleanReferrer) {
    metadata.referrer = cleanReferrer;
  }

  return metadata;
}
