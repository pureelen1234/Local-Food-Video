# E안 — 언리얼 엔진 5.8 · 30초판 (마스터 맥북에서 실행)

- 프로젝트: `/Users/woolim/Documents/Unreal Projects/LocalFoodFilm/LocalFoodFilm.uproject`
- 스크립트는 프로젝트 안 `Scripts/LocalFoodFilm/`에 내려받아 실행합니다.
- 새로 만드는 에셋은 모두 `/Game/LocalFoodFilm/` 아래에 둡니다. 기존 Main 레벨은 건드리지 않습니다.
- 컷 구성은 `../작업일지.md`의 "30초판 컷 구성"을 따릅니다 (토마토가 처음부터 끝까지 이어지는 클로즈업 12컷, 자막 대신 내레이션).

| 순서 | 파일 | 내용 | 상태 |
|---|---|---|---|
| 0 | `lff_00_check.py` | 5.8 파이썬 기능 점검 | ✅ 문제 0개 (09-26) |
| 1 | `lff_01_build.py` | 30초판 전체 조립: 세트 5곳, 인물, 토마토, 카메라 12컷, 내레이션, 슬로건 | 마스터 실행 대기 |
| 2 | `lff_02_render.py` | 무비 렌더 큐 렌더 (ProRes .mov + .wav) | 1단계 확인 후 |
| - | `lff_common.py` | 공통 도우미 (재질, 도형, 시퀀스 키) | |
| - | `lff_run.py` | 실행기 (오류가 나면 창으로 표시) | |
| - | `assets/` | 이름표·슬로건 이미지 (Noto Sans KR로 제작, 한글 깨짐 방지) | |

## 맥북에서 받기
터미널: `curl -fsSL "https://raw.githubusercontent.com/pureelen1234/Local-Food-Video/claude/local-food-video-folder-lopt0m/Local%20Food%20Video/E_Unreal30/sync.sh" | bash`

## 언리얼에서 실행 (맨 아래 Cmd → Python)
`import unreal; LFF_SCRIPT='lff_01_build.py'; exec(open(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())+'Scripts/LocalFoodFilm/lff_run.py', encoding='utf-8').read())`

## 수정하기
- 컷 시간, 카메라 위치: `lff_01_build.py`의 "2. 시퀀스와 컷" 부분
- 이름표·슬로건 글자가 돌아가 보이면: `CARD_ROT` 값
- 내레이션 시작 시각: `NARRATION_START`
