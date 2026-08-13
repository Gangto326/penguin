#!/bin/bash
# Penguin hook 테스트 — 실행: bash tests/test-hooks.sh
# 임시 디렉토리에서 가짜 hook JSON을 흘려보내 카운트·발동·리셋·statusline을 검증한다.
set -u
DIR="$(cd "$(dirname "$0")/.." && pwd)"
COUNT="$DIR/scripts/penguin-count.py"
SL="$DIR/scripts/penguin-statusline.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export CLAUDE_PROJECT_DIR="$TMP"
unset PENGUIN_THRESHOLD 2>/dev/null

pass=0; fail=0
check() { # 이름, 기대(부분 문자열 또는 "없음"), 실제
  local name="$1" expect="$2" actual="$3"
  if { [ "$expect" = "없음" ] && [ -z "$actual" ]; } \
     || { [ "$expect" != "없음" ] && [[ "$actual" == *"$expect"* ]]; }; then
    echo "PASS: $name"; pass=$((pass+1))
  else
    echo "FAIL: $name — 실제 출력: ${actual:-(없음)}"; fail=$((fail+1))
  fi
}
edit() { # 세션id, 파일경로 [, 추가 env는 호출부에서]
  printf '{"session_id":"%s","hook_event_name":"PostToolUse","tool_name":"Edit","tool_input":{"file_path":"%s"}}' \
    "$1" "$2" | python3 "$COUNT"
}
prompt() { printf '{"session_id":"%s","hook_event_name":"UserPromptSubmit"}' "$1" | python3 "$COUNT"; }

# 1) 기본 임계 4: 1~3회 침묵, 4회 발동, 5회 침묵, 6회 재발동
for i in 1 2 3; do check "${i}회째 침묵" "없음" "$(edit s1 /a/f.py)"; done
check "4회째 발동 (additionalContext)" "additionalContext" "$(edit s1 /a/f.py)"
check "5회째 침묵" "없음" "$(edit s1 /a/f.py)"
check "6회째 재발동" "6회 연속 수정" "$(edit s1 /a/f.py)"

# 2) 다른 파일은 독립 카운트
check "다른 파일 1회째 침묵" "없음" "$(edit s1 /a/other.py)"

# 3) UserPromptSubmit 리셋
prompt s1
check "리셋 후 1회째 침묵" "없음" "$(edit s1 /a/f.py)"

# 4) 임계 조정 — 환경 변수
PENGUIN_THRESHOLD=2 edit s2 /a/g.py > /dev/null
check "임계=2, 2회째 발동" "systemMessage" "$(PENGUIN_THRESHOLD=2 edit s2 /a/g.py)"

# 5) 임계 조정 — threshold 파일
mkdir -p "$TMP/.claude/penguin" && echo 3 > "$TMP/.claude/penguin/threshold"
out=""; for i in 1 2 3; do out="$(edit s3 /a/h.py)"; done
check "threshold 파일=3, 3회째 발동" "3회 연속 수정" "$out"
rm "$TMP/.claude/penguin/threshold"

# 6) statusline
check "statusline 카운트 표시" "h.py 3회" \
  "$(printf '{"session_id":"s3","workspace":{"project_dir":"%s"}}' "$TMP" | python3 "$SL")"
check "statusline 상태 없음 → 대기" "🐧 대기" \
  "$(printf '{"session_id":"none","workspace":{"project_dir":"%s"}}' "$TMP" | python3 "$SL")"

# 7) 깨진 입력 내성 (출력 없음 + exit 0)
out="$(echo 'not json' | python3 "$COUNT")"; rc=$?
check "깨진 JSON 무시" "없음" "$out"
check "깨진 JSON exit 0" "0" "$rc"

echo "----------------------------------------"
echo "통과 $pass / 실패 $fail"
[ "$fail" -eq 0 ]
