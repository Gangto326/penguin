#!/usr/bin/env python3
"""PreToolUse — .claude/penguin/config.json 에 해석 불가 값이 저장되는 것을 막는다.

정규화(penguin_config_lib)는 읽는 쪽의 관용이고, 이 hook 은 쓰는 쪽의 검사다.
관용만 있으면 오타("of", "3회")가 조용히 default 로 떨어져 사용자가 "껐다"고
믿는 상태가 생긴다. 여기서 거부하면 그 순간 드러난다.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import penguin_config_lib as cfglib  # noqa: E402

SENTINEL = object()


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


def check(cfg):
    """문제가 있으면 사유 문자열, 없으면 None."""
    if not isinstance(cfg, dict):
        return "config.json 의 최상위는 객체여야 한다."

    problems = []
    for key in ("threshold", "verify_budget"):
        if key not in cfg:
            continue
        minimum = 1 if key == "threshold" else 0
        if key == "verify_budget" and isinstance(cfg[key], str):
            if cfg[key].strip().lower() == "unlimited":
                continue
        if cfglib.as_int(cfg[key], SENTINEL, minimum) is SENTINEL:
            allowed = (
                "1 이상의 정수" if key == "threshold" else '0 이상의 정수 또는 "unlimited"'
            )
            problems.append(f"{key}={json.dumps(cfg[key], ensure_ascii=False)} — {allowed} 여야 한다")

    for key in ("verify_chain", "debt_comments"):
        if key not in cfg:
            continue
        if cfglib.as_bool(cfg[key], SENTINEL) is SENTINEL:
            problems.append(
                f"{key}={json.dumps(cfg[key], ensure_ascii=False)} — true/false 또는 on/off 여야 한다"
            )

    unknown = [k for k in cfg if k not in cfglib.DEFAULTS]
    if unknown:
        problems.append("모르는 키: " + ", ".join(sorted(unknown)))

    if not problems:
        return None
    return (
        "🐧 penguin config.json 에 저장할 수 없는 값이 있다 — "
        + " / ".join(problems)
        + ". 값을 고쳐 다시 저장하라 (해석 불가 값을 그대로 두면 설정이 조용히 무시된다)."
    )


def target_content(tool_name, tool_input):
    """이 도구 호출이 config.json 에 쓰려는 최종 내용. 대상이 아니면 None."""
    path = tool_input.get("file_path") or ""
    if not re.search(r"\.claude[/\\]penguin[/\\]config\.json$", path):
        return None
    if tool_name == "Write":
        return tool_input.get("content") or ""
    if tool_name in ("Edit", "MultiEdit"):
        # 부분 편집은 최종 파일 내용을 알 수 없으므로 현재 파일에 적용해 본다
        try:
            with open(path) as f:
                text = f.read()
        except Exception:
            return None
        edits = (
            [tool_input]
            if tool_name == "Edit"
            else (tool_input.get("edits") or [])
        )
        for e in edits:
            old, new = e.get("old_string") or "", e.get("new_string") or ""
            if old and old in text:
                text = text.replace(old, new, 1)
        return text
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return

    content = target_content(tool_name, data.get("tool_input") or {})
    if content is None:
        return

    try:
        cfg = json.loads(content)
    except Exception:
        deny("🐧 penguin config.json 이 올바른 JSON 이 아니다. 형식을 고쳐 다시 저장하라.")
        return

    reason = check(cfg)
    if reason:
        deny(reason)


if __name__ == "__main__":
    main()
