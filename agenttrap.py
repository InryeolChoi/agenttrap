"""Command-line checks and one-round JSON execution; Streamlit remains independent."""

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys

from game_engine import run_attack
from nosana_client import NosanaError, list_models
from runtime import RuntimeErrorDetail, hello_world


def _print(result):
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="AgentTrap 연결 점검 및 게임 실행")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="API 호출 없이 환경 설정 확인")
    commands.add_parser("models", help="Nosana 모델 목록 조회")
    hello = commands.add_parser("hello", help="Daytona Hello World와 삭제 확인")
    hello.add_argument("--live", action="store_true", help="실제 Sandbox 사용 승인")
    play = commands.add_parser("play", help="Baseline/Attack 실행 후 JSON 출력")
    play.add_argument("--live", action="store_true", help="실제 서비스 및 크레딧 사용 승인")
    inputs = play.add_mutually_exclusive_group()
    inputs.add_argument("--prompt", default="", help="Email C에 추가할 문구 (최대 2000자)")
    inputs.add_argument("--prompt-file", type=Path, help="UTF-8 공격 문구 파일")
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            configured = {name: bool(os.getenv(name)) for name in ("DAYTONA_API_KEY", "NOSANA_API_KEY")}
            ready = all(configured.values())
            _print({"mode": "configuration_only", "ready": ready, "configured": configured,
                    "python": sys.version.split()[0], "packages": {
                        name: version(name) for name in ("daytona", "openai", "streamlit", "pytest")
                    }})
            return 0 if ready else 1
        if args.command == "models":
            _print({"mode": "nosana_models_only", "models": list_models()})
            return 0
        if not args.live:
            raise ValueError("Actual service execution requires --live; credits or Sandbox usage may be billed")
        if args.command == "hello":
            _print(hello_world())
            return 0
        prompt = args.prompt
        if args.prompt_file:
            with args.prompt_file.open(encoding="utf-8") as source:
                prompt = source.read(2001)
        result = run_attack(prompt)
        _print(result)
        return {"EXECUTION_ERROR": 1, "INVALID_TEST": 2}.get(result["verdict"], 0)
    except (ValueError, NosanaError, RuntimeErrorDetail, OSError) as exc:
        _print({"mode": "execution_error", "verdict": "EXECUTION_ERROR", "reason": str(exc),
                "logs": getattr(exc, "__notes__", [])})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
