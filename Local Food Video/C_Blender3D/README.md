# C안 — Blender 3D 버전

무료 3D 프로그램 **Blender**(4.0 이상)의 Python 스크립트로 세트, 인물, 카메라, 자막, 애니메이션을 전부 자동 생성합니다.
언리얼 엔진 계획(기획서)의 구조를 Blender에 맞게 옮겼습니다.

| 기획서(UE5) | C안(Blender) |
|---|---|
| `/Game/LocalFoodFilm/` | `LocalFoodFilm.blend` 하나 (세트별 컬렉션 `SET_*`, `CHARACTERS`, `CAMERAS`) |
| 마스터 시퀀스 + 샷 시퀀스 + Camera Cut 트랙 | 타임라인 마커에 샷 카메라 11대를 연결 (`CAM_S1` ~ `CAM_S8`) |
| `CH_Farmer`, `CH_Staff`, `CH_Consumer` | 같은 이름의 루트 Empty (+ 가족 `CH_Family`, `CH_Child`) |
| JSON 설정 파일 | `config.json` (장면 길이, 자막, 화면 문구, 해상도) |
| MetaHuman | 기본 도형 임시 캐릭터 → 나중에 루트만 교체 |

## 파일 구성
| 파일 | 역할 |
|---|---|
| `config.json` | 장면 길이, 자막, 문구, 렌더 해상도 |
| `scripts/lff_core.py` | 재질, 도형, 한글 글자, 키프레임 도우미 |
| `scripts/lff_char.py` | 임시 3D 인물 5명과 자세(팔, 다리, 고개, 미소) 함수 |
| `scripts/lff_sets.py` | 세트 6곳: 밭, 지도, 직매장, 퇴근길, 저녁 식탁, 엔딩 |
| `scripts/build.py` | 전체 조립: 타임라인, 동작, 카메라, 자막, 장면 전환 → `LocalFoodFilm.blend` |
| `scripts/render.py` | 렌더 (미리보기, 최종, 정지 이미지), 중단 후 이어서 렌더 가능 |
| `assets/fonts/` | Noto Sans KR (겹친 윤곽선을 합쳐서 Blender 한글 깨짐을 방지함, OFL 라이선스) |
| `output/preview_540p.mp4` | 1단계 미리보기 |

## 실행 순서 (맥북에서 직접 할 경우)
1. blender.org 에서 Blender 4.x 설치 (무료)
2. 터미널에서 이 폴더로 이동한 뒤:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python scripts/build.py
/Applications/Blender.app/Contents/MacOS/Blender -b LocalFoodFilm.blend --python scripts/render.py -- preview
/Applications/Blender.app/Contents/MacOS/Blender -b LocalFoodFilm.blend --python scripts/render.py -- final
```
3. `LocalFoodFilm.blend`를 Blender로 열면 장면을 직접 보고 고칠 수 있습니다 (스페이스바로 재생).

## 에셋 교체 방법
- 인물: 새 캐릭터를 불러온 뒤 `CH_Farmer` 등 루트 Empty의 위치와 회전 키프레임을 복사해서 붙이고, 기존 임시 인물 계층은 숨깁니다.
- 자막과 문구: `config.json`만 고치고 `build.py`를 다시 실행하면 됩니다.
- 슬로건은 변경 금지입니다. 원문과 다르면 `build.py`가 멈춥니다.
