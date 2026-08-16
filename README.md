# 🐧 Penguin — 땜빵 루프 탈출 플러그인

오류에 매몰되어 패치를 쌓다 보면 "동작은 하지만 언제 터질지 모르는" 코드가
만들어진다. Penguin은 그 순간을 감지하고, 다음 패치를 만들기 전에 문제를
처음부터 재정의한다.

- **감지는 결정적 계층** — hook이 같은 파일의 연속 수정 횟수를 센다.
  LLM에게 "네가 루프에 있는지 판단하라"고 맡기지 않는다.
- **재검토는 LLM (발산)** — 임계 도달 시 주입되는 넛지를 받아 `/penguin`
  스킬이 내부 분석 6단계(패치 계보 → 전제 검증 → 요구 분해 → 수단
  재탐색 → 매몰 비용 분리 → 판별)를 거쳐 비용 대조 보고서를 출력한다.
  보고서는 창의적 생성물로 취급한다 — 발견이 가치의 원천이고, 서사가
  부풀 수 있다.
- **검증은 분리된 컨텍스트 (냉정)** — 모든 보고서 출력 직후
  `/penguin-verify`가 자동으로 이어 실행되어, 보고서를 쓰지 않은 새
  컨텍스트의 검증자 2종(결론 반박, 독립 사실 조사)으로
  유지/수정/기각/보류를 판정한다. 생성과 검증은 반대 방향의 압력이라
  한 프롬프트에 싣지 않는다.

## 구성

| 파일 | 역할 |
|---|---|
| `skills/penguin/SKILL.md` | 재검토 본체. `/penguin` 직접 호출 + description 기반 자동 발동 |
| `hooks/hooks.json` + `scripts/penguin-count.py` | 파일별 연속 수정 카운터. 임계 도달 시 모델에 넛지 주입 + 사용자에게 🐧 알림 표시. 새 사용자 프롬프트마다 리셋 |
| `scripts/penguin-statusline.py` | (선택) 상태줄에 `🐧 대기` / `🐧 file.py 3회` 표시 |
| `skills/penguin-verify/SKILL.md` | `/penguin-verify` — 보고서 출력 직후 자동 실행되는 분리 검증 (반박자 + 사실 조사자 서브에이전트) |
| `skills/penguin-config/SKILL.md` | `/penguin-config` — 프로젝트 설정 조회·변경 (선택 UI 포함) |
| `skills/penguin-debt/SKILL.md` | `/penguin-debt` — "패치 유지" 결정 시 남기는 `penguin:` 주석을 수확해 장부화 |
| `agents/penguin-verifier.md` | 검증자 전용 에이전트 타입 — 예산 hook의 표적, 읽기 전용 |
| `scripts/penguin-verify-budget.py` | PreToolUse hook — 검증자 도구 호출 예산의 결정적 집행 |
| `scripts/penguin-config-gate.py` | PreToolUse hook — `verify_chain`·`debt_comments` off의 결정적 집행 |
| `scripts/penguin-config-write-guard.py` | PreToolUse hook — config.json에 해석 불가 값이 저장되는 것을 거부 |
| `scripts/penguin_config_lib.py` | 설정 읽기·정규화 공유 모듈 (`on`/`"3"` 같은 표기도 해석, bool→숫자 누수 차단) |
| `benchmarks/measurements.md` | 환경 실측 대장 — 관측과 버전만, 판단 금지. 검증자가 문서 조회 전에 읽는다 |
| `benchmarks/` | 트레이드오프 장부: 이득(백테스트)과 비용(오발동·중단·시간)을 함께 기록. 발동 로그는 `benchmarks/results/log.md` |
| `examples/` | 실제 역사 vs Penguin 백테스트 출력의 before/after 대조 (사례 A·B) |
| `tests/test-hooks.sh` | hook 자가 검증 31케이스 — `bash tests/test-hooks.sh` |

## 언제 발동되나

| 경로 | 상황 |
|---|---|
| 직접 호출 `/penguin` | "왜 이 기능만 계속 고치고 있지" 싶을 때 |
| hook 넛지 (자동) | 한 흐름에서 같은 파일 4회 연속 수정 시 — 사용자가 루프를 인지하지 못해도 발동 |
| description 자동 | 모델이 스스로 반복 수정·상태 변수 증가를 인지했거나, 사용자가 "이 방향이 맞아?"라고 말할 때 |

공통 전제: **이미 패치를 시도한 뒤**여야 한다. 새 기능을 처음 구현 중일
때는 발동하지 않는다.

## 결과물 — 보고서

스킬은 절대 스스로 갈아엎지 않는다. 세 층짜리 보고서를 내고 사용자의
결정을 기다린다: **🐧 한눈 요약**(현상/핵심 원인/권고, 서너 줄) →
**🔍 상황 설명**(코드를 몰라도 이해되는 시간순 서술) → **⚖️ 권고와
대안**(옵션마다 "필요한 행동 / 지금 치르는 것 / 그 후에 남는 것 / 새로
생기는 약점" 병렬 비교). 결함이 없으면 억지 대안 없이 "현 방향이
맞다"로 끝난다.

결정이 "패치 유지"라면 코드에 `# penguin: <남은 전제>, <재검토 트리거>`
주석이 남고, `/penguin-debt`가 이를 수확한다.

**보고서의 검증은 작성자와 분리할 것.** 스킬의 진단을 검증할 때, 보고서를
쓴 세션이 스스로 재검증하면 "사실 확인"에서 멈추거나(확증 편향) 반대로
기각 논거에만 실측을 면제하기(반증 편향) 쉽다 — 실전 사례로 양방향 모두
실증됐다 ([2026-08-14 실전 발동](benchmarks/results/2026-08-14-turn-end-live-case.md)
§5.5). 이 검증을 `/penguin-verify`가 수행한다 — 보고서와 관련 코드
경로만 새 컨텍스트의 검증자 2종에 넘기고 유지/수정/기각/보류를
판정한다. 판별 결과와 무관하게 보고서 출력 직후 자동으로 이어
실행되며(전수 검증 — 실전에서 처방 오류율이 2/2였고, 거짓 "결함 없음"은
hook이 잡지 못하는 수렴 상태에서 나오기 때문), 사용자가 명시적으로
생략을 지시한 경우만 예외다.

## 설치

**방법 1 — marketplace (상시 사용, 권장):**

```
/plugin marketplace add ~/Desktop/Penguin-skill/Penguin
/plugin install penguin@penguin
```

설치 후 `/reload-plugins` 안내가 뜨면 실행. 스킬은 `/penguin` (겹치면
`/penguin:penguin`)으로 호출된다. 소스를 수정했다면
`.claude-plugin/plugin.json`의 version을 올리고
`/plugin marketplace update penguin` 후 재설치해야 반영된다 (설치본은
캐시 복사본이므로).

GitHub에 올린 뒤에는 경로 대신 `owner/repo`로 추가할 수 있다:
`/plugin marketplace add <owner>/<repo>`

**방법 2 — 세션 한정 테스트:**

```bash
claude --plugin-dir ~/Desktop/Penguin-skill/Penguin
```

### statusline (선택)

`~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "/path/to/penguin/scripts/penguin-statusline.py"
  }
}
```

이미 statusline을 쓰고 있다면 기존 스크립트 끝에 이 스크립트 출력을 이어
붙이면 된다.

## 발동 조건

기본 임계는 **같은 파일 4회 연속 수정**(사용자 프롬프트 사이 기준)이고,
도달 이후에도 수정이 계속되면 2회마다 재발동한다.

> 임계 근거: 출발 사례 백테스트에서 적정 발동 시점은 보정 2회째였지만,
> hook은 "실패 후 보정"과 "정상적인 연속 편집"을 구분하지 못하므로
> 오발동을 줄이기 위해 여유를 둔 4로 시작한다. 운영하며 보정할 것.

## 설정 — `/penguin-config`

프로젝트별 설정은 `<프로젝트>/.claude/penguin/config.json` 한 파일이고,
`/penguin-config`로 조회·변경한다 (인자 없이 부르면 선택 UI, `/penguin-config
verify_chain off`처럼 인자로 직접 설정도 가능):

| 키 | 값 | 기본 | 집행 |
|---|---|---|---|
| `threshold` | 1 이상의 정수 | 4 | hook (결정적) |
| `verify_budget` | 0 이상의 정수 또는 `"unlimited"` | 15 | hook (결정적 — 검증 1회당 tool 호출 상한, 초과분 물리 차단) |
| `verify_chain` | true / false | true | hook (결정적 — off면 자동 검증 호출 차단, 수동 `/penguin-verify`는 무관) |
| `debt_comments` | true / false | true | hook (결정적 — off면 `penguin:` 주석 신규 작성 차단) |

값 표기는 관대하고 저장은 엄격합니다: 읽을 때는 `on`/`off`/`"3"` 같은
표기도 해석하지만(`penguin_config_lib`), config.json에 해석 불가 값이
저장되려 하면 쓰기 검증 hook이 거부합니다 — 오타가 "조용히 무시"되는 대신
그 자리에서 드러납니다.

`verify_budget` 감각: 호출 1회 = 파일 읽기·검색·문서 조회 하나. 실측 환산
(실전 2건 기준, 추정)으로 15회 ≈ 검증자당 3만~5만 토큰, 수 분. 0은 조회
없이 보고서 내부 논리만 검증하는 초경량 모드.

환경 변수 `PENGUIN_THRESHOLD`·`PENGUIN_VERIFY_BUDGET`가 있으면 파일보다
우선한다. 레거시 `<프로젝트>/.claude/penguin/threshold` 파일(숫자 한 줄)도
계속 읽힌다 (우선순위: env > config.json > 레거시 파일 > 기본값).

상태 파일은 플러그인 데이터 디렉토리
`~/.claude/plugins/data/penguin/<session_id>.state.json`(hook에는
`CLAUDE_PLUGIN_DATA`로 전달되는 문서화된 경로)에 저장된다. 매 프롬프트마다
7일 넘은 상태 파일이 자동 청소되고, 플러그인 제거 시 디렉토리째 삭제된다.
프로젝트에는 사용자 설정인 `.claude/penguin/threshold`만 남으므로
`.gitignore` 조치가 필요 없다.

## 검증 상태

- hook 단위 테스트 48케이스 (`tests/test-hooks.sh`) — 통과
- hook 실측 PoC 4건 (Claude Code 2.1.231~2.1.233, darwin) — 원문은
  `benchmarks/measurements.md`: Stop hook 발동, PreToolUse의 서브에이전트
  발동·`agent_id` 식별·deny 전달, Skill 도구 호출 차단과 사용자 슬래시
  명령의 hook 우회, AskUserQuestion 입력 제약
- 실세션 e2e: `--plugin-dir` 설치 후 4회 수정 시나리오에서 넛지 발동·
  오발동 경량 통과 확인
- 출발 사례 백테스트 2건: 실제 땜빵 루프 역사의 "패치 도중" 시점을
  블라인드로 주고 실행 → 실제 역사가 우회 끝에 도달한 결론을 더 이른
  시점에 재현 (`benchmarks/results/`)
- 실전 발동 2건: ① 턴 종료 감지 재검토(2026-08-14) — 미검토 공식
  인터페이스 발견과 "실측 먼저" 안전판은 재현, 처방 정밀도는 미달(절반
  과장) → 템플릿 보강 6건(v0.2.0). ② Penguin 자체 상태 파일(2026-08-14)
  — 권고가 분리 검증에서 기각(회상 편향으로 공식 저장 규약을 놓침) →
  4a 문서 실조회 의무와 `/penguin-verify` 신설(v0.3.0). 상세:
  `benchmarks/results/`
