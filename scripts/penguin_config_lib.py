#!/usr/bin/env python3
"""Penguin 설정 읽기·정규화 — hook 3종이 공유한다.

쓰는 쪽(스킬의 LLM, 손으로 편집하는 사용자)이 어떤 표기를 쓰든 읽는 쪽이
해석한다. 해석할 수 없는 값은 조용히 default 로 떨어진다.
"""
import json
import os

TRUE_WORDS = ("on", "true", "yes", "y", "1")
FALSE_WORDS = ("off", "false", "no", "n", "0")

DEFAULTS = {
    "threshold": 4,
    "verify_budget": 15,
    "verify_chain": True,
    "debt_comments": True,
}


def as_bool(value, default):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in TRUE_WORDS:
            return True
        if v in FALSE_WORDS:
            return False
    return default


def as_int(value, default, minimum):
    # bool 은 int 의 하위 타입이라 먼저 걸러낸다 (True 가 1 로 새는 것을 막음)
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value if value >= minimum else default
    if isinstance(value, str):
        v = value.strip()
        if v.isdigit():
            n = int(v)
            return n if n >= minimum else default
    return default


def config_dir(project_dir):
    return os.path.join(project_dir, ".claude", "penguin")


def load_config(project_dir):
    try:
        with open(os.path.join(config_dir(project_dir), "config.json")) as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def state_dir():
    """상태·카운터 저장 위치. hook 은 환경 변수를, statusline 은 고정 경로를 쓴다."""
    return os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.expanduser(
        os.path.join("~", ".claude", "plugins", "data", "penguin")
    )


def threshold(project_dir, cfg=None):
    """우선순위: env > config.json > 레거시 threshold 파일 > 기본 4."""
    default = DEFAULTS["threshold"]
    env = os.environ.get("PENGUIN_THRESHOLD")
    if env is not None:
        return as_int(env, default, 1)
    cfg = load_config(project_dir) if cfg is None else cfg
    if "threshold" in cfg:
        return as_int(cfg["threshold"], default, 1)
    try:
        with open(os.path.join(config_dir(project_dir), "threshold")) as f:
            return as_int(f.read().strip(), default, 1)
    except Exception:
        return default


def verify_budget(project_dir, cfg=None):
    """반환: 정수 상한 또는 None(무제한). 우선순위: env > config.json > 기본 15."""
    default = DEFAULTS["verify_budget"]

    def parse(value):
        if isinstance(value, str) and value.strip().lower() == "unlimited":
            return None
        return as_int(value, default, 0)

    env = os.environ.get("PENGUIN_VERIFY_BUDGET")
    if env is not None and env.strip():
        return parse(env)
    cfg = load_config(project_dir) if cfg is None else cfg
    if "verify_budget" in cfg:
        return parse(cfg["verify_budget"])
    return default


def toggle(key, project_dir, cfg=None):
    """verify_chain·debt_comments — 해석 불가 값은 default(True)."""
    cfg = load_config(project_dir) if cfg is None else cfg
    return as_bool(cfg.get(key), DEFAULTS[key])
