#!/bin/bash
# Penguin hook 테스트 — 실행: bash tests/test-hooks.sh
# 임시 디렉토리에서 가짜 hook JSON을 흘려보내 카운트·발동·리셋·statusline을 검증한다.
set -u
DIR="$(cd "$(dirname "$0")/.." && pwd)"
COUNT="$DIR/scripts/penguin-count.py"
SL="$DIR/scripts/penguin-statusline.py"
BUDGET="$DIR/scripts/penguin-verify-budget.py"
GATE="$DIR/scripts/penguin-config-gate.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export CLAUDE_PROJECT_DIR="$TMP"
export CLAUDE_PLUGIN_DATA="$TMP/plugin-data"
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

# 8) 오래된 상태 파일 청소 (UserPromptSubmit 시, 기준 7일)
mkdir -p "$CLAUDE_PLUGIN_DATA"
touch -t 202001010000 "$CLAUDE_PLUGIN_DATA/old.state.json"
echo '{"counts":{}}' > "$CLAUDE_PLUGIN_DATA/fresh.state.json"
prompt s1
check "7일 넘은 state 삭제" "없음" \
  "$(ls "$CLAUDE_PLUGIN_DATA" | grep '^old\.state\.json$' || true)"
check "최근 state 보존" "fresh.state.json" "$(ls "$CLAUDE_PLUGIN_DATA")"

# 9) 상태 파일이 프로젝트에 생기지 않음
check "프로젝트 내 state 없음" "없음" \
  "$(ls "$TMP/.claude/penguin" 2>/dev/null | grep 'state\.json' || true)"

vb() { # agent_id, agent_type — 검증 예산 hook에 Read 이벤트 주입
  printf '{"session_id":"s9","hook_event_name":"PreToolUse","tool_name":"Read","tool_input":{"file_path":"/x"},"agent_id":"%s","agent_type":"%s"}' \
    "$1" "$2" | python3 "$BUDGET"
}
gate() { printf '%s' "$1" | python3 "$GATE"; }
CFG="$TMP/.claude/penguin/config.json"
mkdir -p "$TMP/.claude/penguin"

# 10) 검증 예산 — 기본 15
out=""; for i in $(seq 1 15); do out="$(vb agA penguin-verifier)"; done
check "예산 기본15, 15회째 허용" "없음" "$out"
check "예산 기본15, 16회째 거부" "deny" "$(vb agA penguin-verifier)"

# 11) 예산 env 오버라이드
PENGUIN_VERIFY_BUDGET=2 vb agB penguin-verifier > /dev/null
PENGUIN_VERIFY_BUDGET=2 vb agB penguin-verifier > /dev/null
check "예산 env=2, 3회째 거부" "deny" "$(PENGUIN_VERIFY_BUDGET=2 vb agB penguin-verifier)"

# 12) config.json 예산 — 0 / unlimited
echo '{"verify_budget":0}' > "$CFG"
check "예산 0, 1회째 거부" "deny" "$(vb agC penguin-verifier)"
echo '{"verify_budget":"unlimited"}' > "$CFG"
out=""; for i in $(seq 1 20); do out="$(vb agD penguin-verifier)"; done
check "예산 unlimited, 20회째 허용" "없음" "$out"
rm "$CFG"

# 13) 예산 표적 아님 — 메인·타 에이전트 무간섭
check "agent_id 없음(메인) 무간섭" "없음" \
  "$(printf '{"session_id":"s9","hook_event_name":"PreToolUse","tool_name":"Read","tool_input":{}}' | python3 "$BUDGET")"
check "타 타입 에이전트 무간섭" "없음" "$(vb agE general-purpose)"

# 14) 게이트 — verify_chain off
echo '{"verify_chain":false}' > "$CFG"
check "chain off: Skill(penguin-verify) 거부" "deny" \
  "$(gate '{"hook_event_name":"PreToolUse","tool_name":"Skill","tool_input":{"skill":"penguin:penguin-verify"}}')"
check "chain off: 다른 스킬 허용" "없음" \
  "$(gate '{"hook_event_name":"PreToolUse","tool_name":"Skill","tool_input":{"skill":"other-skill"}}')"
echo '{"verify_chain":true}' > "$CFG"
check "chain on: Skill(penguin-verify) 허용" "없음" \
  "$(gate '{"hook_event_name":"PreToolUse","tool_name":"Skill","tool_input":{"skill":"penguin:penguin-verify"}}')"

# 15) 게이트 — debt_comments off
echo '{"debt_comments":false}' > "$CFG"
check "comments off: 주석 신규 거부" "deny" \
  "$(gate '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/a.py","old_string":"x = 1","new_string":"x = 1  # penguin: p, t"}}')"
check "comments off: 기존 주석 수정 허용" "없음" \
  "$(gate '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/a.py","old_string":"# penguin: p, t","new_string":"# penguin: p2, t2"}}')"
check "comments off: 일반 편집 허용" "없음" \
  "$(gate '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"old_string":"a","new_string":"b"}}')"
rm "$CFG"

# 16) threshold — config.json 경유
echo '{"threshold":3}' > "$CFG"
out=""; for i in 1 2 3; do out="$(edit s4 /a/i.py)"; done
check "config threshold=3, 3회째 발동" "3회 연속" "$out"
rm "$CFG"

echo "----------------------------------------"
echo "통과 $pass / 실패 $fail"
[ "$fail" -eq 0 ]
