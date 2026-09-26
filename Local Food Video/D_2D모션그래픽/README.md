# D안 — 2D 모션그래픽 버전

HTML(SVG) 애니메이션을 프레임 단위로 캡처해서 MP4로 만드는 방식입니다. 맥북 M1 8GB에서도 돌아갈 만큼 가볍습니다.

## 파일 구성
| 파일 | 역할 |
|---|---|
| `config.json` | **장면 길이·자막·화면 문구 전부** (코드 수정 없이 여기만 고치면 됨) |
| `film.html` | 장면 그림·동작 (장면 8개, 인물 `CH_Farmer` / `CH_Staff` / `CH_Consumer`) |
| `render.js` | 프레임 캡처 → MP4 인코딩, 슬로건 원문 검사, 한글 폰트 로드 검사 |
| `assets/fonts/` | Noto Sans KR (SIL Open Font License, 상업 이용 가능) |
| `output/preview_720p.mp4` | 1단계 미리보기 영상 |
| `output/contact_sheet.png` | 3초 간격 장면 모음 이미지 |

## 수정 방법
- 자막 바꾸기: `config.json` → `scenes[].subtitle`
- 장면 길이 바꾸기: `config.json` → `scenes[].duration` (시작 시각은 자동 계산)
- 생산자 이름표: `config.json` → `labels.producerName`, `labels.producerArea`
- 슬로건은 변경 금지: `render.js`가 원문과 다르면 렌더를 중단함

## 렌더 방법 (맥에서 직접 할 경우)
```bash
brew install node ffmpeg        # 최초 1회
npm install playwright && npx playwright install chromium
node render.js                  # 미리보기 1280x720
node render.js --quality final  # 최종 1920x1080
node render.js --stills 5,30    # 특정 시점 정지 이미지
```
브라우저에서 바로 재생해 보기: 이 폴더에서 `npx serve` 실행 후 `http://localhost:3000/film.html?play` 접속
