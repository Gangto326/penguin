#!/usr/bin/env python3
"""Penguin hook — 같은 파일의 연속 수정을 세고, 임계 도달 시 재검토 넛지를 주입한다.

PostToolUse(Edit|Write 계열): 카운트 증가, 임계 도달 시 additionalContext + systemMessage 출력.
UserPromptSubmit: 카운터 리셋 (새 사용자 프롬프트 = 새 흐름).
"""
import json
import os
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    state_dir = os.path.join(project_dir, ".claude", "penguin")
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

    def threshold():
        # 우선순위: 환경 변수 PENGUIN_THRESHOLD > .claude/penguin/threshold 파일 > 기본 4
        v = os.environ.get("PENGUIN_THRESHOLD", "")
        if v.strip().isdigit():
            return int(v)
        try:
            with open(os.path.join(state_dir, "threshold")) as f:
                return int(f.read().strip())
        except Exception:
            return 4

    if event == "UserPromptSubmit":
        save_state({"counts": {}})
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
