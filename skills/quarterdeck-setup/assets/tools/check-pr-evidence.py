#!/usr/bin/env python3
"""A pull request body carries every section of the evidence block, or it is not reviewable.

Workflow section 8: the body of an agent pull request is written so that reviewing it requires
running nothing. A missing section is ambiguity; the tier-2 decisions section in particular is
mandatory even when it reads "none".

Reads the body on stdin, or fetches it with `--pr <number>` through the `gh` CLI:

    printf '%s' "$PR_BODY" | python3 tools/quarterdeck/check-pr-evidence.py
    python3 tools/quarterdeck/check-pr-evidence.py --pr 42

Exit 0 when every section is present and every acceptance line is ticked with evidence, 1 when
not, 2 when the body could not be read.
"""

import argparse
import re
import subprocess
import sys

SECTIONS = ['Task', 'Acceptance', 'Verification', 'Architecture', 'Decisions made (tier 2)', 'Not done']


def read_body(pr: str) -> str:
    if pr:
        result = subprocess.run(['gh', 'pr', 'view', pr, '--json', 'body', '--jq', '.body'],
                                capture_output=True, text=True)
        if result.returncode != 0:
            print(f'gh pr view failed: {result.stderr.strip()}', file=sys.stderr)
            sys.exit(2)
        return result.stdout
    return sys.stdin.read()


def section(body: str, title: str) -> str:
    """The text under `## <title>` up to the next `## ` heading, or None when absent."""
    match = re.search(r'^##\s+' + re.escape(title) + r'\s*$(.*?)(?=^##\s|\Z)', body, re.M | re.S | re.I)
    return match.group(1) if match else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--pr', help='pull request number to read through gh')
    args = parser.parse_args()
    body = read_body(args.pr)
    if not body.strip():
        print('the pull request body is empty', file=sys.stderr)
        sys.exit(1)

    problems = []
    for title in SECTIONS:
        text = section(body, title)
        if text is None:
            problems.append(f'missing section: ## {title}')
        elif not text.strip():
            problems.append(f'empty section: ## {title} (write "none" if there is nothing)')

    acceptance = section(body, 'Acceptance') or ''
    lines = [line for line in acceptance.splitlines() if line.strip().startswith('- [')]
    if acceptance and not lines:
        problems.append('Acceptance lists no criteria')
    for line in lines:
        if not line.strip().startswith('- [x]'):
            problems.append(f'acceptance criterion not ticked: {line.strip()}')
        elif ' — ' not in line and ' - ' not in line.split(']', 1)[1]:
            problems.append(f'acceptance criterion carries no evidence after a dash: {line.strip()}')

    if problems:
        print('the evidence block is incomplete:')
        for problem in problems:
            print(f'  {problem}')
        sys.exit(1)
    print(f'evidence block complete: {len(SECTIONS)} sections, {len(lines)} acceptance criteria with evidence')
    sys.exit(0)


if __name__ == '__main__':
    main()
