#!/bin/bash
# 맥북에서 실행: GitHub 의 최신 스크립트·이미지를 언리얼 프로젝트로 내려받는다.
BASE="https://raw.githubusercontent.com/pureelen1234/Local-Food-Video/claude/local-food-video-folder-lopt0m/Local%20Food%20Video/E_Unreal30/Scripts/LocalFoodFilm"
DEST="$HOME/Documents/Unreal Projects/LocalFoodFilm/Scripts/LocalFoodFilm"
mkdir -p "$DEST/assets"
for f in lff_common.py lff_run.py lff_00_check.py lff_01_build.py lff_02_render.py assets/T_LFF_NameTag.png assets/T_LFF_Slogan.png; do
  curl -fsSL -o "$DEST/$f" "$BASE/$f" && echo "받음: $f" || echo "실패: $f"
done
# 내레이션 aiff → wav 변환 (있을 때만)
for a in "$HOME/Desktop/내레이션"/nar_0*.aiff; do
  [ -f "$a" ] && afconvert -f WAVE -d LEI16 "$a" "${a%.aiff}.wav" && echo "변환: $(basename "${a%.aiff}.wav")"
done
echo "완료"
