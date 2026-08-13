# Examples — 실제 역사 vs Penguin이 있었다면

같은 상황을 Penguin 없이(실제 역사) / 있이(백테스트 출력) 나란히 놓은
대조. 백테스트 출력은 손으로 쓴 게 아니라 블라인드 시나리오를 준 에이전트의
실제 출력이다. 방법과 한계: [../benchmarks/results/](../benchmarks/results/)

| 사례 | Penguin 없이 | Penguin 있었다면 |
|---|---|---|
| [A. 세션 전환](case-a-session-switch.md) | 패치 5겹, ~하루 우회, 죽은 기능 잠복 | 패치 2 시점에 "전제 미실측" 경보 → rewrite 권고 |
| [B. 판례 해석](case-b-precedent-gate.md) | 프롬프트 설득 방향, 확률적 검증 | "MUST를 LLM에 맡겼다" 지적 → 결정적 필터 권고 |
