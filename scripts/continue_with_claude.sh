#!/bin/sh
set -eu

printf '%s\n' '--- Git status ---'
git status --short --branch
printf '%s\n' '--- Last commit ---'
git log -1 --oneline 2>/dev/null || printf '%s\n' 'No commits yet.'
if [ -f HANDOFF.md ]; then
  printf '%s\n' '--- HANDOFF.md ---'
else
  printf '%s\n' 'HANDOFF.md is missing; create it before continuing.'
  exit 1
fi
if command -v claude >/dev/null 2>&1; then
  exec claude
fi
printf '%s\n' 'Claude Code is not installed or not on PATH. Install it from https://docs.anthropic.com/en/docs/claude-code/overview'
exit 127
