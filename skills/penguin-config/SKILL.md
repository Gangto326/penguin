---
name: penguin-config
description: >
  Penguin 플러그인의 프로젝트 설정을 보여주고 바꾼다 — 재검토를 권할
  연속 수정 횟수(threshold), 검증 조회 예산(verify_budget), 보고서 후
  자동 검증(verify_chain), 패치 유지 주석(debt_comments). "펭귄 설정",
  "/penguin-config", "검증 예산 바꿔 줘", "자동 검증 꺼 줘" 등에
  사용한다. 설정 파일만 수정하며 다른 일은 하지 않는다.
argument-hint: "[키] [값]"
---

# 🐧⚙️ Penguin Config

설정 파일: `<프로젝트>/.claude/penguin/config.json` — 없으면 기본값이
유효하다.

## 키와 값 (단일 기준 — 다른 절은 이 표를 참조만 한다)

| 키 | 허용 값 | default | config.json 기록 타입 | 집행 |
|---|---|---|---|---|
| `threshold` | 1 이상의 정수 | `4` | 숫자 | hook (결정적) |
| `verify_budget` | 0 이상의 정수 또는 `unlimited` | `15` | 숫자 또는 `"unlimited"` | hook (결정적 — 초과 조회 차단) |
| `verify_chain` | true / false | `true` | 불리언 | hook (결정적 — 자동 호출 차단, 수동 `/penguin-verify` 는 무관) |
| `debt_comments` | true / false | `true` | 불리언 | hook (결정적 — 주석 신규 작성 차단) |

**기록 타입을 지켜라** — 사용자가 `on`/`off`/`"3"` 로 말해도 파일에는
`true`/`false`/`3` 으로 기록한다. hook 은 문자열 표기도 해석하지만, 사람이
읽거나 다른 도구가 파싱할 때 흔들리므로 표의 타입으로 통일한다.

**해석 불가 값은 default 로 기록**하고 그 사실을 한 줄로 알린다:
`threshold: "abc" 는 잘못된 값 → 4 (default)`. `"5회"`·`"on "` 처럼
공백·단위만 붙은 값은 숫자·불리언으로 정리해 받아들이고, 그 외의 해석은
하지 마라 — 애매하면 default 다.

읽기 우선순위는 **env > config.json > 레거시 `.claude/penguin/threshold`
파일 > default** 다 (hook 도 같은 순서를 쓴다) — 현재값을 보여줄 때 이
순서를 따르지 않으면 화면과 실제 동작이 어긋난다. env 가 설정돼 있으면
파일을 바꿔도 env 가 이긴다는 것을 사용자에게 알려라.

## 인자가 있으면 ($ARGUMENTS)

`/penguin-config <키> <값>` — 묻지 말고 해당 키만 검증해 기록하고,
`verify_budget: 15 → 30` 처럼 **한 줄만** 출력한다.

## 인자가 없으면

**설명·표·서문을 출력하지 마라.** 위 우선순위대로 현재값을 조용히 읽고,
곧바로 AskUserQuestion 을 띄운다. 현재값은 옵션 라벨에 넣어 보여준다.

한 번의 호출에 네 항목을 각각의 질문으로 함께 묻는다. 옵션 구성:

- `verify_budget` — `0` / `15` / `30` / `50` 네 개를 이 순서로 고정한다.
  `unlimited` 와 그 밖의 숫자는 자유 입력란으로 받는다. 현재값이 넷 중
  하나가 아니면(예: `unlimited`, `7`) 순서는 그대로 두고 `(현재)` 는 어느
  옵션에도 붙이지 않는다 — 대신 질문 문구 끝에 `(현재: unlimited)` 를
  덧붙여 알린다.
- `verify_chain` — `on` / `off`
- `debt_comments` — `on` / `off`
- `threshold` — 아래 규칙대로 구성

**문구** — 물음표 문장을 쓰지 마라. 아래 명사구를 그대로 쓰고, 설명은
붙이지 않는다:

| 키 | header | question 자리에 넣을 문구 |
|---|---|---|
| `verify_budget` | 검증 예산 | 검증 시 tool 호출 제한 |
| `verify_chain` | 자동 검증 | 보고서 직후 자동 검증 실행 |
| `debt_comments` | 유지 주석 | 패치 유지 시 `penguin:` 주석 작성 |
| `threshold` | 자동 호출 | penguin 자동 호출 임계값 |

**현재값·default 표시** (`verify_budget`·`verify_chain`·`debt_comments`)
— 옵션 목록의 **순서는 위 구성대로 두고**, 표시만 붙인다. 현재값에
해당하는 옵션에 `(현재)`. 현재값이 default 와 **같으면 그 옵션에
`(현재)` 만** 쓰고 어디에도 `(default)` 를 쓰지 않는다. **다르면**
현재값 옵션에 `(현재)`, default 값 옵션에 `(default)` 를 각각 붙인다.
그 밖의 옵션은 라벨만 둔다. (`threshold` 는 아래 별도 규칙을 따른다.)

**옵션 설명** — on/off 항목(`verify_chain`·`debt_comments`)에만 짧게
붙인다. 숫자 항목(`verify_budget`·`threshold`)은 설명 자리에 공백 한 칸
`" "` 을 넣어 줄 간격만 유지한다.

**`threshold` 옵션 구성** (다른 항목과 규칙이 다르다):

- 1번 옵션 = 현재값. 현재값이 default 와 같으면 `4 (현재)`, 다르면 `6`
  처럼 그 숫자로 쓴다.
- 2번 옵션 = 항상 `4 (default)`. 1번과 값이 같아도 그대로 둔다 — 한
  질문 안에서 **동일한 라벨 두 개는 하네스가 거부**하므로(실측:
  `benchmarks/measurements.md`) 1번은 `(현재)`, 2번은 `(default)` 로
  구분해 라벨이 겹치지 않게 한다.
- 그 밖의 숫자를 원하는 사용자는 하네스가 자동 제공하는 자유 입력란을
  쓴다 — **"직접 입력" 같은 옵션을 만들지 마라** (같은 일을 한 단계 더
  거치게 만든다).

env 로 고정된 항목은 라벨에 `(env 고정)` 을 붙인다.

답변 라벨에서 `(현재)`·`(default)`·`(env 고정)` 접미사를 벗겨 **값만**
꺼낸 뒤 위 표의 기록 타입으로 변환한다 (`on` → `true`, `"30"` → `30`).
현재값과 다른 항목만 config.json 에 **병합 저장**(다른 키
보존, 디렉토리 없으면 생성)하고, **변경된 줄만** 한 줄씩 보고한다
(`verify_budget: 15 → 30`). 변경이 없으면 "변경 없음" 한 줄. env 가 파일을
가리는 경우에만 그 사실을 한 줄 덧붙인다.

## 경계

- 이 스킬은 설정 파일만 만진다 — 코드·스킬·다른 설정을 수정하지 않는다.
- 레거시 `<프로젝트>/.claude/penguin/threshold` 파일이 있으면 편입 제안을
  변경 보고 끝에 **한 줄로만** 덧붙이고, 사용자가 동의할 때만 실행한다.
- 설정을 설명하거나 조언하지 마라 — 사용자가 물으면 그때 답한다.
