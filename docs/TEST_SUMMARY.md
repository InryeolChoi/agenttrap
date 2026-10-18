# 자동 테스트 89개 검증 요약

## 기록 기준

2026-10-18 레벨링 구현 중 전체 테스트 **89개 통과**를 확인했습니다. 매개변수별 실행 사례를 각각 1개로 세며 테스트 함수 개수와 다릅니다. 이후 서버 TTL로 이미 삭제된 컨테이너의 정리 처리를 검증하는 1개를 추가해, PR #15의 최종 결과는 **90개 통과**입니다.

기준 코드: 레벨링 PR #15, 커밋 `a6c5568` 및 병합 커밋 `8cbbb26`. 이 문서의 89개는 TTL 삭제 처리 사례를 추가하기 직전의 검증 범위이며, 현재 저장소에 존재하는 테스트 총수는 90개입니다.

## 파일별 요약

| 테스트 파일 | 89개 검증 시 사례 수 | 핵심 검증 내용 |
| --- | ---: | --- |
| `tests/test_app.py` | 8 | 초기 화면, 결과·도구 시도 표시, 오류·알 수 없는 모드 구분, HTML 이스케이프, Mock, 빈 입력, Retry 초기화 |
| `tests/test_cli.py` | 3 | Hello World 실행·정리, 실제 실행 승인 플래그, 키 값 비노출 설정 점검 |
| `tests/test_game_engine.py` | 12 | 필수 키 사전 확인, 도구 한도, Baseline 기록 보존, JSON 오류, 승패·무효 판정, 공격 문자열의 데이터 처리 |
| `tests/test_judge.py` | 8 | 필수 요약·3개 이메일 읽기, 위험·미등록 도구 시도, 업무 실패, Baseline 무효, 시도와 실행 구분 |
| `tests/test_level_sessions.py` | 7 | 같은 레벨 컨테이너 재사용, Baseline·Attack 동일 방어 설정, 잘못된 레벨 사전 차단, 만료·오류 정리, 삭제 재시도, 입문 프로토콜 |
| `tests/test_level_ui.py` | 4 | 실제 경로 성공 결과의 다음 레벨 해금, Retry 재사용·Mock 비해금, 3단계 클리어·초기화, 삭제 실패 시 이동 차단 |
| `tests/test_levels.py` | 9 | LIVE 공격 성공만 해금, Mock·알 수 없는 모드·방어 승리·무효·오류·잘못된 레벨은 유지, 중복 결과 멱등성, 최종 클리어 |
| `tests/test_nosana_client.py` | 16 | 지정 주소·모델, 모델 조회·선택, 응답 검증, 클라이언트 정리, 안전한 오류, 개별 노드 계정 키 차단, HTTPS, 추론 예산 |
| `tests/test_runtime.py` | 22 | 이메일 사실 보존, 읽기 후 추론, 위험 도구 차단, 생성·실행·출력·삭제 오류, 출력 제한, 비공개·네트워크 차단·TTL·키 비전달 |
| **합계** | **89** | **레벨링과 기존 게임 기능의 회귀 검증** |

## 이후 추가된 1개

`tests/test_level_sessions.py::test_already_deleted_container_can_close_after_server_ttl`

서버 TTL로 컨테이너가 이미 삭제돼 Daytona SDK가 `DaytonaNotFoundError`를 반환해도, 정리 완료로 처리해 다음 세션 시작을 막지 않는지 확인합니다. 이 사례를 포함한 현재 `test_level_sessions.py`는 8개, 전체는 90개입니다.

## 실행과 해석

```sh
.venv/bin/python -m pytest -q
# 최종 실행 기록: 90 passed in 4.38s

.venv/bin/python -m pytest --collect-only -q
# 문서 작성 시 확인: 90 tests collected
```

외부 Nosana·Daytona SDK 경계는 테스트 대역을 사용합니다. Sandbox의 고정 실행기 코드는 로컬 격리 Python 서브프로세스에서 실행합니다. 기존 UI 표시 테스트는 엔진 결과 대역을 사용하고, 새 레벨 UI 통합 테스트는 실제 엔진·Judge·진행 정책을 연결한 상태에서 외부 SDK만 대체합니다.

자동 테스트 통과는 실제 GLM의 공격 성공률이나 모든 레벨의 실제 클리어를 증명하지 않습니다. 실제 서비스 검증은 다음 기록과 구분합니다.

- [GLM 실제 UI 공격 성공](evidence/2026-10-18-glm-ui/README.md)
- [레벨 컨테이너 실제 재사용과 UI 재도전](evidence/2026-10-18-levels/README.md)
