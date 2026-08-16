#!/usr/bin/env python3
"""PreToolUse — penguin-verifier 서브에이전트의 도구 호출 예산 집행.

메인 에이전트(stdin에 agent_id 없음)와 다른 서브에이전트는 건드리지 않는다.
예산 우선순위: PENGUIN_VERIFY_BUDGET 환경 변수 > .claude/penguin/config.json
의 verify_budget > 기본 15. 값은 0(조회 금지)/양의 정수/"unlimited".
초과 시 permissionDecision=deny 로 거부하고 "미탐색으로 분류하고 마무리
하라"는 지시를 모델에 전달한다 (사유는 deny 시 모델에게 전달됨 — 공식
hook 문서 보장).
"""
import json
import os
import sys

DEFAULT_BUDGET = 15


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    agent_id = data.get("agent_id")
    agent_type = data.get("agent_type") or ""
    # agent_id 존재 = 서브에이전트 (공식 구분 필드). 검증자 타입만 표적.
    if not agent_id or "penguin-verifier" not in agent_type:
        return

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."

    def budget():
        # 반환: 정수 상한, 또는 None(무제한)
        v = os.environ.get("PENGUIN_VERIFY_BUDGET", "").strip()
        if v:
            if v.lower() == "unlimited":
                return None
            if v.isdigit():
                return int(v)
        try:
            with open(
                os.path.join(project_dir, ".claude", "penguin", "config.json")
            ) as f:
                b = json.load(f).get("verify_budget")
            if b == "unlimited":
                return None
            if isinstance(b, int) and b >= 0:
                return b
        except Exception:
            pass
        return DEFAULT_BUDGET

    state_dir = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.expanduser(
        os.path.join("~", ".claude", "plugins", "data", "penguin")
    )
    counter_path = os.path.join(state_dir, f"verify-{agent_id}.count")
    try:
        with open(counter_path) as f:
            count = int(f.read().strip())
    except Exception:
        count = 0
    count += 1
    try:
        os.makedirs(state_dir, exist_ok=True)
        with open(counter_path, "w") as f:
            f.write(str(count))
    except OSError:
        return  # 카운터를 못 쓰면 집행 불능 — 조용히 허용 (검증 자체를 막지 않는다)

    limit = budget()
    if limit is None or count <= limit:
        return

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"🐧 검증 조회 예산({limit}회)을 초과했다. 추가 도구 호출 없이, "
                        "확인하지 못한 항목은 '미탐색'으로 분류하고 지금까지의 "
                        "결과만으로 최종 보고를 출력하라."
                    ),
                }
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
