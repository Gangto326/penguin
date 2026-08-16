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
유효하다.

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

`/penguin-config <키> <값>` — 해당 키만 검증해 기록하고 "변경 전 → 후"를
한 줄로 보고한다. boolean 은 on/off/true/false 를 받는다.
`verify_budget` 은 다섯 단계(0·15·30·50·unlimited)만 허용 — 다른 값이
오면 기록하지 말고 다섯 단계를 안내하라.

## 인자가 없으면

1. config.json 과 환경 변수를 읽어 **현재 유효값과 출처**(기본값 / 파일 /
   env)를 표로 보여준다.
2. AskUserQuestion 으로 바꿀 항목을 고르게 한다 (복수 선택 허용, "그대로
   두기" 포함). 선택된 항목마다 값을 묻는다:
   - `verify_budget`: 옵션 [15 (기본) / 30 / 50 / unlimited]. 0(조회
     없이 보고서 내부 논리만 검증)을 원하면 "Other"에 0 입력을 안내.
   - `verify_chain`·`debt_comments`: on / off.
   - `threshold`: 옵션 [3 / 4 (기본) / 6] + 직접 입력은 Other.
3. 선택을 config.json 에 **병합 저장**(다른 키 보존, 디렉토리 없으면
   생성)하고 결과 표를 다시 보여준다.

## 경계

- 이 스킬은 설정 파일만 만진다 — 코드·스킬·다른 설정을 수정하지 않는다.
- 레거시 `<프로젝트>/.claude/penguin/threshold` 파일이 있으면 config.json
  으로의 편입(값 이동 후 파일 삭제)을 제안하되, 사용자가 동의할 때만
  실행한다.
