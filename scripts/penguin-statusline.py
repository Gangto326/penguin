#!/usr/bin/env python3
"""Penguin statusline — 현재 세션의 최다 연속 수정 파일을 상태줄에 표시한다.

stdin: Claude Code statusline JSON (session_id, workspace.project_dir 포함)
"""
import json
import os
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print("🐧 대기")
        return

    workspace = data.get("workspace") or {}
    project_dir = (
        workspace.get("project_dir")
        or workspace.get("current_dir")
        or data.get("cwd")
        or "."
    )
    config_dir = os.path.join(project_dir, ".claude", "penguin")
    # hook(penguin-count.py)과 같은 상태 경로를 재구성한다 — statusline 에는
    # CLAUDE_PLUGIN_DATA 가 보장되지 않으므로 동일한 고정 폴백을 쓴다.
    state_dir = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.expanduser(
        os.path.join("~", ".claude", "plugins", "data", "penguin")
    )
    session_id = data.get("session_id") or "default"
    state_path = os.path.join(state_dir, f"{session_id}.state.json")

    def threshold():
        v = os.environ.get("PENGUIN_THRESHOLD", "")
        if v.strip().isdigit():
            return int(v)
        try:
            with open(os.path.join(config_dir, "config.json")) as f:
                t = json.load(f).get("threshold")
            if isinstance(t, int) and t > 0:
                return t
        except Exception:
            pass
        try:
            with open(os.path.join(config_dir, "threshold")) as f:
                return int(f.read().strip())
        except Exception:
            return 4

    try:
        with open(state_path) as f:
            counts = json.load(f).get("counts", {})
    except Exception:
        counts = {}

    if not counts:
        print("🐧 대기")
        return

    top_file, top_count = max(counts.items(), key=lambda kv: kv[1])
    name = os.path.basename(top_file)
    mark = " ⚠️" if top_count >= threshold() else ""
    print(f"🐧 {name} {top_count}회{mark}")


if __name__ == "__main__":
    main()
