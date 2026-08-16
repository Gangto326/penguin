# 환경 실측 대장

> **관측만 적는다 — 판단·권고는 쓰지 마라.** 무엇을 했고 무엇이 나왔는지,
> 그리고 `claude --version`과 날짜를 반드시 병기한다.
>
> **각 항목은 그 시점의 관측이다.** 현재 버전이 다르면 무효로 보고 다시
> 측정하라. 이 파일이 재탐색을 대신하는 권위가 되면, 4a("기억으로 답하지
> 마라")가 막으려던 것과 같은 함정이 된다.

---

## 2026-08-14 · Claude Code 2.1.231 (darwin 25.2.0) · Stop hook

방법: scratch 프로젝트 `.claude/settings.json` 에 Stop hook 등록(stdin 덤프),
pexpect 로 실TUI 기동(haiku, 45×160), 짧은 턴 → 긴 턴 2회.

- Stop hook 은 대화형 TUI 에서 매 턴 정확히 1회 발동했다. busy 마커가
  렌더되지 않는 짧은 턴에서도 발동했다.
- stdin 필드: `session_id`, `transcript_path`, `cwd`, `prompt_id`,
  `permission_mode`, `hook_event_name`, `stop_hook_active`,
  `last_assistant_message`, `background_tasks`, `session_crons`.
- 턴 1 발동 시점에 `last_assistant_message` 는 그 턴의 응답을 담고 있었으나,
  같은 시점의 transcript 에는 해당 assistant 이벤트가 아직 없었다
  (`last_assistant_at_fire: null`). 턴 2 발동 시점에야 턴 1 응답이 보였다.
- 원자료: `benchmarks/results/2026-08-14-turn-end-live-case.md` 부록 A.

## 2026-08-16 · Claude Code 2.1.233 (darwin 25.2.0) · PreToolUse × 서브에이전트

방법: scratch 프로젝트에 PreToolUse hook(matcher `*`, stdin 덤프) 등록 →
`claude --model haiku -p "...서브에이전트를 띄워 Read·Bash 를 쓰게 하라..."`.

- 서브에이전트의 도구 호출에도 PreToolUse 가 발동했다 (이벤트 3건: 메인의
  `Agent` 호출 1 + 서브의 `Read` 1 + `Bash` 1).
- 서브에이전트 이벤트에만 `agent_id`(예: `ae041e691b8026576`)와
  `agent_type`(`general-purpose`)이 있었다. 메인 에이전트 이벤트에는 두
  필드가 **없었다**.
- `session_id`·`prompt_id`·`transcript_path` 는 메인과 서브가 동일했다.
- 공통 필드: `cwd`, `hook_event_name`, `permission_mode`, `prompt_id`,
  `session_id`, `tool_input`, `tool_name`, `tool_use_id`, `transcript_path`.
- 환경 변수로 `CLAUDE_PROJECT_DIR` 가 hook 프로세스에 전달됐다.

## 2026-08-16 · Claude Code 2.1.233 (darwin 25.2.0) · deny 집행

방법: 위 hook 을 "서브에이전트 도구 호출 2회 초과 시
`permissionDecision: deny`" 로 바꾸고, 서브에이전트에게 도구 호출 4회를
순서대로 시도시켰다.

- 1·2회차(Read, Bash)는 실행됐고, 3회차(Bash)는 거부됐다.
- 거부 사유(`permissionDecisionReason`) 원문이 서브에이전트에게 전달됐고,
  서브에이전트가 그 문구를 그대로 보고했다.
- 4회차는 시도조차 하지 않고 "미탐색 (도구 호출 예산 초과로 시도 불가)"로
  분류한 뒤 최종 보고를 냈다.

## 2026-08-16 · Claude Code 2.1.233 (darwin 25.2.0) · Skill 도구 호출과 슬래시 명령

방법: scratch 에 더미 스킬을 두고 ① 모델에게 "Skill 도구로 호출하라" ②
사용자 프롬프트로 `/dummy-skill` 입력, 두 경로를 각각 실행.

- ① 모델의 호출은 PreToolUse 에 잡혔다: `tool_name: "Skill"`,
  `tool_input: {"skill": "dummy-skill"}`.
- ② 사용자가 타이핑한 슬래시 명령은 hook 이벤트를 **발생시키지 않았다**
  (이벤트 0건).
- ①을 `permissionDecision: deny` 로 막자 스킬은 로드되지 않았고, 모델은
  거부 사유에 담긴 안내 문구를 그대로 출력했다.

## 2026-08-16 · Claude Code 2.1.233 (darwin 25.2.0) · AskUserQuestion 입력 제약

방법: 이 저장소 작업 중 AskUserQuestion 도구를 실제로 호출하며 관측.

- 한 질문 안에 동일한 라벨 두 개(`4 (default)` × 2)를 넣자 호출이 거부됐다:
  `InputValidationError: Question texts must be unique, option labels must be
  unique within each question`.
- 도구 스키마상 옵션은 질문당 최소 2개, 최대 4개이며, 옵션의 `label` 과
  `description` 은 모두 필수 필드다.
- "Other"(자유 입력) 항목은 하네스가 자동으로 붙이며, 도구 설명이 직접
  넣지 말라고 명시한다.
- 공식 문서(code.claude.com/docs/en/tools)에는 이 도구의 입력 스키마 기술이
  없었다 — 위 제약의 출처는 도구 스키마와 실제 호출 오류다.
