type MenuImageInput = {
  name: string;
  imageUrl?: string | null;
  category?: string | null;
};

const productionApiOrigin = "https://picky-chatbot-production.up.railway.app";

const generatedFoodImageBase = "/foods/generated";

const localFoodImagesByName: Record<string, string> = {
  김치찌개: `${generatedFoodImageBase}/kimchi-jjigae-v2.jpg`,
  순두부찌개: `${generatedFoodImageBase}/sundubu-jjigae-v2.jpg`,
  제육덮밥: `${generatedFoodImageBase}/jeyuk-deopbap-v2.jpg`,
  마라탕: `${generatedFoodImageBase}/malatang-v2.jpg`,
  돈까스: `${generatedFoodImageBase}/donkatsu-v2.jpg`,
  쌀국수: `${generatedFoodImageBase}/pho-v2.jpg`,
  김밥: `${generatedFoodImageBase}/kimbap.jpg`,
  국밥: `${generatedFoodImageBase}/gukbap-v2.jpg`,
  떡볶이: `${generatedFoodImageBase}/tteokbokki.jpg`,
  파스타: `${generatedFoodImageBase}/pasta.jpg`,
  삼겹살: `${generatedFoodImageBase}/samgyeopsal.jpg`,
  비빔밥: `${generatedFoodImageBase}/bibimbap.jpg`,
  오므라이스: `${generatedFoodImageBase}/omurice.jpg`,
  카레라이스: `${generatedFoodImageBase}/curry-rice.jpg`,
  초밥: `${generatedFoodImageBase}/sushi.jpg`,
  연어덮밥: `${generatedFoodImageBase}/salmon-deopbap.jpg`,
  칼국수: `${generatedFoodImageBase}/kalguksu.jpg`,
  라멘: `${generatedFoodImageBase}/ramen.jpg`,
  잔치국수: `${generatedFoodImageBase}/janchi-guksu.jpg`,
  냉면: `${generatedFoodImageBase}/naengmyeon.jpg`,
};

const localFoodImagesByCategory: Record<string, string> = {
  찌개: localFoodImagesByName.김치찌개,
  국물: localFoodImagesByName.순두부찌개,
  국밥: localFoodImagesByName.국밥,
  덮밥: localFoodImagesByName.제육덮밥,
  마라: localFoodImagesByName.마라탕,
  튀김: localFoodImagesByName.돈까스,
  면: localFoodImagesByName.쌀국수,
  고기: localFoodImagesByName.삼겹살,
  분식: localFoodImagesByName.김밥,
  밥: localFoodImagesByName.비빔밥,
};

function resolveBackendImageUrl(imageUrl: string | null | undefined, apiBaseUrl: string) {
  if (!imageUrl) {
    return null;
  }

  try {
    const url = new URL(imageUrl, apiBaseUrl);
    const apiUrl = new URL(apiBaseUrl);
    const isLocalPreview = apiUrl.hostname === "localhost" || apiUrl.hostname === "127.0.0.1";

    if (isLocalPreview && url.origin === productionApiOrigin) {
      return `${apiUrl.origin}${url.pathname}`;
    }

    return url.toString();
  } catch {
    return imageUrl;
  }
}

export function getMenuImageUrl(item: MenuImageInput, apiBaseUrl: string) {
  const backendImageUrl = resolveBackendImageUrl(item.imageUrl, apiBaseUrl);

  if (backendImageUrl) {
    return backendImageUrl;
  }

  return localFoodImagesByName[item.name] ?? (item.category ? localFoodImagesByCategory[item.category] : null) ?? null;
}
