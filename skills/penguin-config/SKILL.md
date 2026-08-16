---
name: penguin-config
description: >
  Penguin 플러그인의 프로젝트 설정을 보여주고 바꾼다 — 넛지 임계
  (threshold), 검증 조회 예산(verify_budget), 보고서 후 자동 검증
  (verify_chain), 패치 유지 주석(debt_comments). "펭귄 설정",
  "/penguin-config", "검증 예산 바꿔 줘", "자동 검증 꺼 줘" 등에
  사용한다. 설정 파일만 수정하며 다른 일은 하지 않는다.
argument-hint: "[키] [값]"
---

# 🐧⚙️ Penguin Config

설정 파일: `<프로젝트>/.claude/penguin/config.json` — 없으면 기본값이
유효하다. 이 스킬의 출력은 설정 화면과 변경 결과뿐이다 — 아래 표와 설명은
너를 위한 참고 자료이지 사용자에게 보여줄 내용이 아니다.

| 키 | 허용 값 | 기본 | 집행 방식 |
|---|---|---|---|
| `threshold` | 양의 정수 | 4 | hook (결정적) |
| `verify_budget` | 0 / 15 / 30 / 50 / "unlimited" | 15 | hook (결정적 — 초과 조회 차단) |
| `verify_chain` | true / false | true | hook (결정적 — 자동 호출 차단, 수동 `/penguin-verify` 는 무관) |
| `debt_comments` | true / false | true | hook (결정적 — 주석 신규 작성 차단) |

환경 변수 `PENGUIN_THRESHOLD`·`PENGUIN_VERIFY_BUDGET` 이 설정돼 있으면
파일보다 우선한다 — 그 경우 파일을 바꿔도 env 가 이긴다는 것을
사용자에게 알려라.

## 인자가 있으면 ($ARGUMENTS)

`/penguin-config <키> <값>` — 묻지 말고 해당 키만 검증해 기록하고,
`verify_budget: 15 → 30` 처럼 **한 줄만** 출력한다. boolean 은
on/off/true/false 를 받는다. `verify_budget` 은 다섯 단계(0·15·30·50·
unlimited)만 허용 — 다른 값이 오면 기록하지 말고 다섯 단계를 한 줄로
안내하라.

## 인자가 없으면

**설명·표·서문을 출력하지 마라.** config.json 과 환경 변수를 조용히 읽고,
곧바로 AskUserQuestion 을 띄운다. 현재값은 옵션 라벨에 넣어 보여준다.

한 번의 호출에 네 항목을 각각의 질문으로 함께 묻는다 (각 질문의 첫 옵션은
현재값이며 라벨 끝에 `(현재)`):

- `verify_budget` — 15 / 30 / 50 / 0 / unlimited
- `verify_chain` — on / off
- `debt_comments` — on / off
- `threshold` — 3 / 4 / 6

각 질문의 `description` 은 한 줄 이내로 짧게. env 로 고정된 항목은 라벨에
`(env 고정)` 을 붙인다.

답변을 받으면 현재값과 다른 항목만 config.json 에 **병합 저장**(다른 키
보존, 디렉토리 없으면 생성)하고, **변경된 줄만** 한 줄씩 보고한다
(`verify_budget: 15 → 30`). 변경이 없으면 "변경 없음" 한 줄. env 가 파일을
가리는 경우에만 그 사실을 한 줄 덧붙인다.

## 경계

- 이 스킬은 설정 파일만 만진다 — 코드·스킬·다른 설정을 수정하지 않는다.
- 레거시 `<프로젝트>/.claude/penguin/threshold` 파일이 있으면 편입 제안을
  변경 보고 끝에 **한 줄로만** 덧붙이고, 사용자가 동의할 때만 실행한다.
- 설정을 설명하거나 조언하지 마라 — 사용자가 물으면 그때 답한다.
