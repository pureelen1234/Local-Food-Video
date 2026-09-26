#!/bin/bash
# 맥북 내장 한국어 음성으로 30초판 내레이션 파일을 만든다 (미리보기용).
# 사용법: 터미널에서  bash make_tts_mac.sh        (음성을 직접 고르려면: bash make_tts_mac.sh "Yuna")
# 결과: out/nar_01.aiff ~ nar_05.aiff  (언리얼 시퀀스에서 각 시작 시각에 배치)
cd "$(dirname "$0")" || exit 1
VOICE="$1"
if [ -z "$VOICE" ]; then
  VOICE=$(say -v '?' | grep 'ko_KR' | head -1 | sed -E 's/ +ko_KR.*//')
fi
if [ -z "$VOICE" ]; then
  echo "한국어 음성이 없습니다."
  echo "시스템 설정 > 손쉬운 사용 > 읽기 및 말하기 > 시스템 음성 > 음성 관리 에서 '한국어 - 유나'를 추가한 뒤 다시 실행하세요."
  exit 1
fi
echo "사용 음성: $VOICE"
echo "사용 가능한 한국어 음성 목록:"; say -v '?' | grep 'ko_KR'
mkdir -p out
i=0
while IFS=$'\t' read -r start end text; do
  [ -z "$text" ] && continue
  i=$((i+1))
  f=$(printf "out/nar_%02d.aiff" "$i")
  say -v "$VOICE" -r 175 -o "$f" "$text"
  dur=$(afinfo "$f" | awk '/estimated duration/{print $3}')
  slot=$(echo "$end - $start" | bc)
  ok=$(echo "$dur <= $slot" | bc)
  flag="OK"; [ "$ok" = "1" ] || flag="길이 초과!"
  echo "[$flag] $i번  ${start}~${end}초(${slot}초)  음성 ${dur}초  $text"
done < lines.tsv
echo "완료: $(pwd)/out"
say -v "$VOICE" -r 175 "미리 듣기를 시작합니다."
for f in out/nar_*.aiff; do afplay "$f"; done
