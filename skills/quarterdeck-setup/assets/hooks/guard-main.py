#!/usr/bin/env python3
"""Refuse the git operations that belong to a human.

Workflow section 9: the main branch is not an agent's to write, no branch is an agent's to merge
or rewrite, and a pull request is not an agent's to merge. Those rules are also in the agent
instructions, but a rule in prose is one a model can talk itself out of — this one fails the tool
call instead.

The main branch and the task-branch prefix are read from `.quarterdeck.json` in the project root
at each call, so this file is identical in every project and never needs re-rendering.

Reads the PreToolUse payload on stdin. Exit 0 allows, exit 2 blocks and returns the reason to the
agent. Anything unexpected allows: a guard that breaks the session teaches people to remove it.
"""

import json
import os
import re
import shlex
import subprocess
import sys

PROJECT = os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()


def manifest() -> dict:
    try:
        with open(os.path.join(PROJECT, '.quarterdeck.json'), encoding='utf-8') as handle:
            return json.load(handle)
    except Exception:
        return {}


_M = manifest()
MAIN = _M.get('main_branch') or 'main'
TASK_PREFIX = _M.get('task_prefix') or 'task/'
WORKFLOW = f"{(_M.get('docs_dir') or 'docs/workflow').rstrip('/')}/workflow.md"

# Rewriting history or merging is never an agent's job, on any branch.
ALWAYS = {
    'merge': 'merging is the owner\'s',
    'rebase': 'rebasing rewrites history',
    'filter-branch': 'rewriting history',
    'cherry-pick': 'replaying commits onto another branch',
}

# On the main branch, everything that writes is the owner's.
ON_MAIN = {
    'commit': f'commit on your own `{TASK_PREFIX}*` branch',
    'push': f'push your own `{TASK_PREFIX}*` branch',
    'reset': f'resetting `{MAIN}` discards the owner\'s work',
    'revert': f'reverting on `{MAIN}` is a commit',
    'am': f'applying patches to `{MAIN}` is a commit',
}


def deny(reason: str, fix: str) -> None:
    print(f'Blocked by .claude/hooks/guard-main.py: {reason}.\n{fix}', file=sys.stderr)
    sys.exit(2)


def strip_heredocs(command: str) -> str:
    """Remove heredoc bodies so prose about git is not mistaken for running git."""
    out, lines, i = [], command.split('\n'), 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        match = re.search(r'<<-?\s*[\'"]?([A-Za-z_][A-Za-z0-9_]*)[\'"]?', line)
        i += 1
        if not match:
            continue
        end = match.group(1)
        while i < len(lines) and lines[i].strip() != end:
            i += 1
        i += 1  # the delimiter line itself
    return '\n'.join(out)


def segments(command: str):
    """Split a command line into the individual commands it runs."""
    for part in re.split(r'&&|\|\||[;\n|]', command):
        try:
            tokens = shlex.split(part)
        except ValueError:
            tokens = part.split()
        while tokens and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*', tokens[0]):
            tokens = tokens[1:]
        if tokens:
            yield tokens


def current_branch() -> str:
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, timeout=5,
            cwd=PROJECT,
        )
    except Exception:
        return ''
    return result.stdout.strip() if result.returncode == 0 else ''


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if payload.get('tool_name') != 'Bash':
        sys.exit(0)
    command = (payload.get('tool_input') or {}).get('command') or ''
    branch = current_branch()

    for tokens in segments(strip_heredocs(command)):
        program = os.path.basename(tokens[0])
        args = [token for token in tokens[1:] if token != '--']
        words = [a for a in args if not a.startswith('-')]
        sub = words[0] if words else ''

        if program == 'gh' and words[:2] == ['pr', 'merge']:
            deny('`gh pr merge` — merging a pull request is the owner\'s',
                 'Leave it in `in review` and say so; the owner merges by hand.')
        if program != 'git':
            continue
        if sub in ALWAYS:
            deny(f'`git {sub}` — {ALWAYS[sub]}',
                 'Ask the owner instead, or work it out on your own task branch without rewriting history.')
        if sub == 'push':
            if any(a in ('--force', '-f', '--force-with-lease', '--mirror', '--delete', '-d') for a in args) \
               or any(a.startswith('+') for a in words[1:]):
                deny('a force or delete push', 'Push the branch normally; nothing else is yours to move.')
            if any(w == MAIN or w.endswith(f':{MAIN}') for w in words[1:]):
                deny(f'a push to `{MAIN}`', f'Push your `{TASK_PREFIX}*` branch and open a pull request.')
        # A branch switch earlier in the same command line applies to what follows it.
        if sub in ('checkout', 'switch') and len(words) > 1:
            branch = words[-1]
            continue
        if branch == MAIN and sub in ON_MAIN:
            deny(f'`git {sub}` while on `{MAIN}` — {ON_MAIN[sub]}',
                 f'Create `{TASK_PREFIX}<task-id>-<slug>` first: see {WORKFLOW} section 7.')

    sys.exit(0)


if __name__ == '__main__':
    main()
