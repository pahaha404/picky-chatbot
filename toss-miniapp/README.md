# toss-miniapp

Apps in Toss 프로젝트입니다.

## 시작하기

```bash
npm run dev
```

## 배포하기

- 앱인토스 배포 API 키는 [앱인토스 콘솔](https://apps-in-toss.toss.im/) > 워크스페이스 > API 키 > 콘솔 API 키 에서 발급받을 수 있어요.

```bash
npm run build
npm run deploy
```

## 성장 지표

공유 버튼은 공유 URL에 `ref`, `utm_source=share`, `utm_medium=toss_miniapp`을 붙입니다.
앱이 열리면 `/api/toss/events`의 `app_open` 이벤트 metadata에 유입 출처가 함께 기록됩니다.

```bash
npm run test:growth
```

## 유용한 링크

- [앱인토스 콘솔](https://apps-in-toss.toss.im/)
- [앱인토스 개발자센터](https://developers-apps-in-toss.toss.im/)
- [앱인토스 개발자 커뮤니티](https://techchat-apps-in-toss.toss.im/)

AI를 사용하시는 경우 [여기](https://developers-apps-in-toss.toss.im/development/llms.html)를 확인해보세요.
