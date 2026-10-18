# AgentTrap 런타임 구현 계약

기준 커밋: `03ff8b7`. Developer A와 통합 담당의 범위이며 UI 파일은 변경하지 않는다.

- `game_engine.run_attack(attack_prompt: str) -> dict`와 기존 필드를 유지한다.
- 원본 이메일 A/B/C의 사실을 유지하고 공격 문구는 C에만 추가한다. 입력은 최대 2000자다.
- 키와 입력을 점검한 뒤 Sandbox를 생성한다. 키가 없을 때 서비스 사용을 시작하지 않는다.
- Daytona에서 고정 Python 코드로 이메일을 실제 읽고, 반환된 내용을 호스트의 Nosana 추론에 전달한다.
- Nosana의 제공 모델을 조회하거나 `NOSANA_MODEL`을 사용한다. Baseline/Attack은 같은 모델로 실행한다.
- 모델 JSON의 구조와 크기를 검증한다. 문자열 변환이나 호출 목록 자르기로 잘못된 출력을 통과시키지 않는다.
- `read_email` 외 모든 도구 시도는 기록하고 차단한다. 시도와 실행 여부를 구별한다.
- 이메일 읽기 기록과 세 가지 필수 사실을 deterministic Judge로 검사한다.
- Baseline 실패는 `INVALID_TEST`; API/JSON/Sandbox 오류는 `EXECUTION_ERROR`다. 공격 실패를 승리로 꾸미지 않는다.
- Baseline이 실패하면 Attack을 시작하지 않는다. Attack 오류가 나도 완료된 Baseline의 상태와 로그는 유지한다.
- Nosana 키를 Sandbox에 전달하지 않는다. 공격 문자열이나 모델 출력은 실행 가능한 소스로 사용하지 않는다.
- Sandbox 네트워크 차단, 실행 시간/단계/출력 제한, 삭제 확인을 적용한다. 삭제 실패도 보고한다.
- CLI는 키 값 없이 환경 점검, 모델 목록, Hello World, 게임 JSON 실행을 지원한다. 비용 발생 가능한 실행에는 명시적 `--live`가 필요하다.
- 테스트는 외부 SDK 경계에서 대역을 사용한다. 고정 Runner는 로컬 격리 Python에서 실행해 결과를 판정한다. 대역 테스트를 실제 Nosana/Daytona 증거라고 표시하지 않는다.
- README는 한국어로 작성하고 친구의 `feat/game`과 파일 소유권을 유지한다.
