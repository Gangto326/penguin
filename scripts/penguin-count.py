#!/usr/bin/env python3
"""Penguin hook — 같은 파일의 연속 수정을 세고, 임계 도달 시 재검토 넛지를 주입한다.

PostToolUse(Edit|Write 계열): 카운트 증가, 임계 도달 시 additionalContext + systemMessage 출력.
UserPromptSubmit: 카운터 리셋 (새 사용자 프롬프트 = 새 흐름) + 오래된 상태 파일 청소.

상태는 플러그인 데이터 디렉토리(CLAUDE_PLUGIN_DATA)에, 사용자 설정(threshold)은
프로젝트 .claude/penguin/ 에 둔다 — 상태는 수명이 한 흐름인 임시 데이터,
설정은 영속 데이터라 위치가 다르다.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import penguin_config_lib as cfglib  # noqa: E402

# 상태 수명은 "한 프롬프트 흐름"(매 프롬프트 리셋)이라 청소 기준은 세션보다
# 길기만 하면 되고, 오삭제의 비용은 카운트 리셋 1회뿐이다.
STALE_DAYS = 7


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    # statusline 프로세스에는 CLAUDE_PLUGIN_DATA 환경 변수가 보장되지 않으므로,
    # 폴백은 두 스크립트가 동일하게 재구성할 수 있는 문서화된 고정 경로여야 한다.
    state_dir = cfglib.state_dir()
    session_id = data.get("session_id") or "default"
    state_path = os.path.join(state_dir, f"{session_id}.state.json")
    event = data.get("hook_event_name", "")

    def load_state():
        try:
            with open(state_path) as f:
                return json.load(f)
        except Exception:
            return {"counts": {}}

    def save_state(state):
        os.makedirs(state_dir, exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(state, f, ensure_ascii=False)

    def cleanup_stale_states():
        cutoff = time.time() - STALE_DAYS * 86400
        try:
            names = os.listdir(state_dir)
        except OSError:
            return
        for name in names:
            # 세션 상태와 검증 예산 카운터를 함께 수거한다
            if not name.endswith((".state.json", ".count")):
                continue
            if name == f"{session_id}.state.json":
                continue
            path = os.path.join(state_dir, name)
            try:
                if os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except OSError:
                pass

    def threshold():
        return cfglib.threshold(project_dir)

    if event == "UserPromptSubmit":
        save_state({"counts": {}})
        cleanup_stale_states()
        return

    if event != "PostToolUse":
        return

    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not file_path:
        return

    state = load_state()
    counts = state.setdefault("counts", {})
    counts[file_path] = counts.get(file_path, 0) + 1
    count = counts[file_path]
    save_state(state)

    limit = threshold()
    # 임계 도달 시 발동, 이후에도 수정이 계속되면 2회마다 재발동
    if count < limit or (count - limit) % 2 != 0:
        return

    name = os.path.basename(file_path)
    to_model = (
        f"🐧 Penguin: '{file_path}' 파일이 이번 흐름에서 {count}회 연속 수정되었다. "
        "땜빵 루프 신호일 수 있다. 다음 패치를 만들기 전에 penguin 스킬을 실행해 "
        "패치 계보와 전제를 재검토하라. 정상적인 연속 작업(수렴 중)이라면 "
        "각 수정의 전제가 실측된 사실임을 확인하고 계속하라."
    )
    to_user = f"🐧 Penguin: {name} {count}회 연속 수정 — 재검토 권고"
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": to_model,
                },
                "systemMessage": to_user,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
