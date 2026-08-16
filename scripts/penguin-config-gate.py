#!/usr/bin/env python3
"""PreToolUse — penguin 설정 토글의 결정적 집행 (verify_chain, debt_comments).

- verify_chain=false: 모델이 Skill 도구로 penguin-verify 를 자동 호출하는
  것을 거부한다. 사용자가 직접 타이핑한 /penguin-verify 는 hook 을 타지
  않으므로(실측 확인) 수동 실행은 영향 없다.
- debt_comments=false: Edit/Write 계열로 `penguin:` 주석을 **새로** 쓰는
  것을 거부한다. 기존 주석이 포함된 구간의 수정(old 에도 존재)은 허용.
"""
import json
import os
import re
import sys

MARKER = re.compile(r"(#|//|/\*|<!--|--)\s*penguin:")


def load_config(project_dir):
    try:
        with open(
            os.path.join(project_dir, ".claude", "penguin", "config.json")
        ) as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def deny(reason):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )


def adds_marker(tool_name, tool_input):
    """새로 추가되는 내용에만 penguin: 마커가 있는가 (기존 구간 수정은 제외)."""
    pairs = []
    if tool_name == "Write":
        pairs.append((tool_input.get("content") or "", ""))
    elif tool_name == "NotebookEdit":
        pairs.append((tool_input.get("new_source") or "", ""))
    elif tool_name == "Edit":
        pairs.append(
            (tool_input.get("new_string") or "", tool_input.get("old_string") or "")
        )
    elif tool_name == "MultiEdit":
        for e in tool_input.get("edits") or []:
            pairs.append((e.get("new_string") or "", e.get("old_string") or ""))
    for new, old in pairs:
        if MARKER.search(new) and not MARKER.search(old):
            return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    cfg = load_config(project_dir)

    if tool_name == "Skill" and cfg.get("verify_chain") is False:
        if "penguin-verify" in str(tool_input.get("skill", "")):
            deny(
                "🐧 자동 검증이 설정으로 꺼져 있다(verify_chain=off). 스킬을 "
                "호출하지 말고, 보고서 끝에 '자동 검증 꺼짐 — `/penguin-verify` 로 "
                "수동 실행 가능'이라고만 안내하라."
            )
            return

    if cfg.get("debt_comments") is False and tool_name in (
        "Edit",
        "Write",
        "MultiEdit",
        "NotebookEdit",
    ):
        if adds_marker(tool_name, tool_input):
            deny(
                "🐧 penguin 주석이 설정으로 꺼져 있다(debt_comments=off). 이 "
                "편집에서 `penguin:` 주석 줄을 빼고 다시 수행하라."
            )
            return


if __name__ == "__main__":
    main()
