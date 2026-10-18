# 친구의 AI 에이전트에게 전달할 프롬프트

저장소: https://github.com/InryeolChoi/agenttrap (Public)
쓰기 권한 초대 대상: `pang0916` — push 전에 초대를 수락하세요.

아래 내용을 친구의 AI 에이전트에게 그대로 전달하세요.

```text
너는 AgentTrap의 Developer B다. 목표는 기존 게임 엔진을 사용하는 Streamlit UI 구현이다.
저장소: https://github.com/InryeolChoi/agenttrap
담당 이슈: https://github.com/InryeolChoi/agenttrap/issues/3 (선행 이슈 없이 시작 가능)

먼저 AGENTS.md, HANDOFF.md, README.md를 읽고 git status --short --branch를 확인하라.

[작업 공간과 브랜치]
- Developer A와 별도의 로컬 clone에서 작업한다. 같은 디렉터리에서 브랜치를 바꾸며 작업하지 않는다.
- 새 clone: gh repo clone InryeolChoi/agenttrap
- clone한 디렉터리에서 git fetch origin 후 git switch --track origin/feat/game을 실행한다.
- 이미 feat/game 로컬 브랜치가 있으면 git switch feat/game을 사용한다.
- 미커밋 변경이 있으면 보존하고, 다른 사람의 변경을 초기화하거나 덮어쓰지 않는다.
- main과 feat/runtime에는 커밋하지 않는다. force push, reset --hard, git clean, 다른 브랜치 삭제를 금지한다.

[수정 가능한 파일]
- app.py
- tests/test_app.py
이 두 파일만 수정한다. runtime.py, nosana_client.py, game_engine.py, judge.py, scenarios.py,
requirements.txt, 기존 테스트, AGENTS.md, CLAUDE.md, HANDOFF.md 등 공유 파일은 수정하지 않는다.
의존성이나 계약 변경이 필요하면 변경안을 보고하고 담당자가 반영하도록 한다.

[고정 인터페이스]
from game_engine import run_attack
result = run_attack(attack_prompt)  # attack_prompt는 str

반환 필드:
- mode: live 또는 execution_error (UI fixture는 mock)
- baseline_status: PASS / FAIL / UNKNOWN
- security_pass, task_pass: bool
- verdict: DEFENDER_WINS / ATTACKER_WINS / INVALID_TEST / EXECUTION_ERROR
- reason: 설명 문자열
- tool_calls: name, attempted, executed를 가진 레코드 목록. email_id가 추가될 수 있다.
- summary: meeting, deadline, project 필드를 가진 dict
- logs: 문자열 또는 {round, entries} 형식의 레코드 목록
추가 필드가 생겨도 UI는 동작해야 한다.

[화면 요구사항]
공격 프롬프트 입력, Attack 버튼, 실행 중 표시, Defender 로그, 도구 호출 시도/실행 여부,
Security 결과, Task 결과, 최종 승패와 이유, Retry를 표시한다.
Attack 클릭 시에만 run_attack을 호출한다. Streamlit 재실행으로 API가 중복 호출되지 않도록
session_state에 마지막 결과를 보관한다. Retry는 로컬 화면 상태를 초기화하며 API를 자동 호출하지 않는다.
INVALID_TEST와 EXECUTION_ERROR를 공격 승리로 표시하지 않는다.
결과의 mode를 그대로 표시하고, mock을 live로 바꾸거나 공격 성공을 하드코딩하지 않는다.
UI에 API 키 입력/노출 기능을 만들지 않는다.

[API 없이 구현하는 방법]
scenarios.mock_result()를 fixture로 사용하거나 테스트에서 run_attack을 대체한다.
개발용 mock을 화면에 제공한다면 mock임을 명확히 표시한다.
Judge나 시나리오 생성 로직을 UI에 복제하지 않는다.

[검증과 전달]
README에 따라 프로젝트 전용 .venv를 사용한다.
UI 테스트는 tests/test_app.py에만 추가하고 실제 API나 Sandbox를 호출하지 않게 한다.
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q
.venv/bin/python -m streamlit run app.py
테스트가 통과하면 본인 소유 파일만 명시적으로 git add하고 feat/game에 커밋 및 push한다.
main 병합은 통합 담당자가 수행한다.
완료 보고에는 브랜치, 커밋 ID, 변경 파일, 테스트 결과, 필요한 계약 변경을 적는다.
```
