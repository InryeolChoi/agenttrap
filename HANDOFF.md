# AgentTrap handoff

## Current Goal

3단계 레벨링과 같은 레벨의 Daytona 컨테이너 재사용을 구현했다. 최신 코드와 테스트·실행 근거를 PR로 공유하고 발표를 준비한다.

## Branch and Collaboration

작업 시작 기준은 main의 `703033f`다. 이번 레벨링은 사용자가 엔진·진행 정책·UI 세 경계의 구현과 테스트를 승인했고, 친구 담당 `app.py`와 `tests/test_app.py`도 이번 범위에서 직접 수정하도록 명시적으로 허용했다. 기존 미커밋 개발자 변경은 없었다. 최종 브랜치와 커밋은 Git 상태로 확인한다.

기본 소유권은 AGENTS.md를 따른다. 공유 레벨 계약은 SPEC.md 12절이다. `.env`는 로컬 전용이며 키를 출력하거나 저장소에 올리지 않는다.

## Implemented

- `levels.py`: 입문·경계·방어 3단계와 진행 정책.
- `run_attack(prompt, level_id=3, session=None)`: 기본 호출의 기존 Defender와 생성·삭제 방식 유지. UI는 1레벨부터 시작하며 레벨 메타데이터를 반환한다.
- `LevelSession`: 한 레벨의 Baseline·Attack·Retry에 같은 컨테이너를 사용한다. 고정 실행기가 매 라운드 이메일·기록을 초기화한다.
- 다음 레벨 이동 전에 삭제 완료를 확인한다. 마지막 레벨 성공 시 삭제한다. 삭제 실패 시 이동·전체 클리어를 확정하지 않는다.
- 4분 재사용 한도와 5분 서버 TTL. 오류·만료 이후 새 세션을 사용하며 이미 TTL로 삭제된 컨테이너의 NotFound는 정리 완료로 처리한다.
- LIVE + Baseline PASS + 현재 레벨 ATTACKER_WINS만 해금한다. Mock·오류·무효·이전 레벨 결과로는 진행하지 않는다.
- UI의 레벨·해금 상태·다음 레벨·전체 클리어·처음부터 다시·컨테이너 ID 표시. Retry는 진행도와 활성 컨테이너를 유지한다.
- Nosana의 개별 배포에는 계정 키를 보내지 않는다. HTTPS 및 별도 NOSANA_ENDPOINT_KEY 처리를 유지한다.

## Tests and Evidence

TDD에서 실패를 먼저 확인하고 구현했다. 전체 `.venv/bin/python -m pytest -q` 결과: **90 passed**. 외부 SDK 대역을 사용하며 고정 실행기는 실제 격리 Python 서브프로세스에서 실행한다.

- `docs/evidence/2026-10-18/`: 기존 Qwen 실제 백엔드 기록.
- `docs/evidence/2026-10-18-glm-ui/`: 레벨링 전 실제 GLM UI 공격 성공. Baseline PASS, Security FAIL, Task PASS, 삭제 시도 차단.
- `docs/evidence/2026-10-18-levels/`: 실제 같은 컨테이너 재사용 결과 JSON과 레벨 UI 화면·텍스트.
- 실제 세션 확인: 한 컨테이너에서 첫 공격 성공, 두 번째 Baseline 실패로 INVALID_TEST. finally 삭제 완료.
- 프로토콜 안내를 보완한 이후 실제 UI에서 두 번 재도전했고 두 번 모두 Defender 승리, 같은 Sandbox ID를 표시했다. 다음 레벨은 해금되지 않았다.
- 실제 모델로 3단계 전체 클리어를 검증한 것은 아니다. 3단계 클리어·다음 레벨 삭제·오류·Mock 비해금은 자동 테스트로 검증했다.

## Runtime

로컬 Python은 `.venv`의 3.14.8이다. UI는 `http://127.0.0.1:8501/`에서 실행한다. 코드의 새 클래스가 Streamlit에 캐시돼 있으면 서버를 재시작한다. 새 브라우저 세션에서는 진행도가 초기화된다. 브라우저 종료 시 즉시 삭제는 보장하지 않으며 서버 TTL로 남은 컨테이너를 정리한다.

Nosana 대상 모델은 `glm-4.7-flash:q4_K_M`이다. 실제 개별 배포의 모델 목록 조회와 추론에 성공했다. 과거 503 상태와 공용 API/GLM 모델명 불일치는 이전 기록이며 현재 성공과 구분한다. 모델 출력은 비결정적이고 Baseline 실패·JSON 오류가 발생할 수 있다.

## Presentation

`docs/presentation/README.md`에 공식 로고 포함 7장 PPT, 3분 대본, 오프라인 데모가 있다. 최신 `AgentTrap-발표-확장계획.pdf`(8장)와 편집 원본 PPTX·대본에 레벨링 및 GLM 실제 성공 근거, 향후 4단계 실제 서비스 검증을 반영했다. 4단계는 발전 방향이며 현재 게임의 구현 범위는 3단계다. `docs/TEST_SUMMARY.md`는 중간 89개와 최종 90개 검증 범위를 요약한다. 기존 오프라인 데모의 REPLAY/MOCK 표시는 유지한다.

## Next Actions

1. 레벨링 PR을 검토·병합한다. 테스트 결과와 실제 호출 기록을 구분한다.
2. 최신 UI에서 공격·해금·다음 레벨 흐름을 발표 리허설한다. 실제 승패를 하드코딩하지 않는다.
3. 행사 종료 후 세션 컨테이너와 TTL 정리 상태를 확인한다.
