#!/usr/bin/env python3
"""Print a session transcript as a readable timeline, for /retro.

    python3 .claude/skills/retro/digest.py                the newest session of this project — the one running now
    python3 .claude/skills/retro/digest.py <id-prefix>    a session by its id, or a path to its .jsonl
    python3 .claude/skills/retro/digest.py --pr <n>       the session that opened pull request <n>
    python3 .claude/skills/retro/digest.py --list [n]     the n most recent sessions (default 15): id, start, branch, title

Claude Code keeps transcripts in ~/.claude/projects/<repository path, every non-alphanumeric as
"-">/, and a session run in a worktree under .claude/worktrees/ in a sibling directory with a
longer name — both are searched. CLAUDE_CONFIG_DIR is honoured. Another agent keeps no transcript
here, and the helper says so.

Every tool call and every result carries its time, so the gap between them is how long the call
took. Long text is cut — a user turn at 600 characters, the agent's text at 400, a tool call or its
result at 200 — and a cut line says how long it was, so a result that filled the context shows as
one. ERROR marks a failed tool call; BLOCKED marks a refusal by a hook.

Python 3.9+, standard library only.
"""

import glob
import json
import os
import re
import subprocess
import sys

SKILL_LOADED = 'Base directory for this skill:'
HOOK_REFUSAL = re.compile(r'hook error|^Blocked by')


def transcripts_dir() -> str:
    try:
        common = subprocess.run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                                capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit('Not inside a git repository.')
    slug = re.sub(r'[^A-Za-z0-9]', '-', os.path.dirname(common))
    config = os.environ.get('CLAUDE_CONFIG_DIR') or os.path.join(os.path.expanduser('~'), '.claude')
    return os.path.join(config, 'projects', slug)


def sessions() -> list:
    base = transcripts_dir()
    found = glob.glob(os.path.join(base, '*.jsonl')) + glob.glob(base + '--*' + os.sep + '*.jsonl')
    return sorted(found, key=os.path.getmtime, reverse=True)


def lines(path: str):
    with open(path, encoding='utf-8', errors='replace') as handle:
        yield from handle


# A substring test before json: a transcript runs to tens of megabytes, and only a few of its
# lines are wanted.
def describe(path: str) -> str:
    start = branch = title = ''
    for line in lines(path):
        if not start:
            found = re.search(r'"timestamp":"([^"]*)"', line)
            start = found.group(1)[:16] if found else ''
        found = re.findall(r'"gitBranch":"([^"]*)"', line)
        branch = found[-1] if found else branch
        if '"type":"custom-title"' in line:
            title = json.loads(line).get('customTitle') or title
    session = os.path.basename(path)[:-len('.jsonl')]
    return f'{session}  {start or "?"}  {branch or "?"}  {title or "(untitled)"}'


def clip(text: str, limit: int) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text[:limit] + f'… [{len(text)} chars]' if len(text) > limit else text


def flatten(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ' '.join(item['text'] for item in content if isinstance(item, dict) and 'text' in item)
    return ''


def timeline(path: str):
    printed = set()
    for line in lines(path):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get('isSidechain'):
            continue
        kind = entry.get('type')
        stamp = '[' + (entry.get('timestamp') or '')[11:19] + ']'
        content = (entry.get('message') or {}).get('content')
        if kind == 'user' and isinstance(content, str):
            yield f'\n{stamp} USER: {clip(content, 600)}'
        elif kind == 'user':
            for block in content or []:
                if block.get('type') == 'text' and block['text'].startswith(SKILL_LOADED):
                    name = re.search(r'skills/([^/\s]+)', block['text'])
                    yield f'  .. skill loaded: {name.group(1) if name else "?"}'
                elif block.get('type') == 'text':
                    yield f'\n{stamp} USER: {clip(block["text"], 600)}'
                elif block.get('type') == 'tool_result':
                    out = flatten(block.get('content'))
                    if block.get('is_error') and HOOK_REFUSAL.search(out):
                        yield f'  <- {stamp} BLOCKED {clip(out, 300)}'
                    elif block.get('is_error'):
                        yield f'  <- {stamp} ERROR {clip(out, 300)}'
                    else:
                        yield f'  <- {stamp} {clip(out, 200)}'
        elif kind == 'assistant':
            for block in content or []:
                if block.get('type') == 'text':
                    yield f'{stamp} AGENT: {clip(block["text"], 400)}'
                elif block.get('type') == 'tool_use':
                    call = json.dumps(block.get('input'), ensure_ascii=False, separators=(',', ':'))
                    yield f'  -> {stamp} {block.get("name")} {clip(call, 200)}'
        elif kind == 'pr-link':
            link = f'  == PR #{entry.get("prNumber")} {entry.get("prUrl")}'
            if link not in printed:
                printed.add(link)
                yield link


def pick(args: list) -> str:
    if args and args[0] == '--pr':
        if len(args) < 2 or not args[1].isdigit():
            sys.exit('usage: digest.py --pr <number>')
        needle = f'"prNumber":{args[1]},'
        return next((f for f in sessions() if any(needle in line for line in lines(f))), '')
    if args and os.path.isfile(args[0]):
        return args[0]
    found = sessions()
    if args:
        found = [f for f in found if os.path.basename(f).startswith(args[0])]
    return found[0] if found else ''


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    if args and args[0] == '--list':
        count = int(args[1]) if len(args) > 1 else 15
        for path in sessions()[:count]:
            print(describe(path))
        return
    path = pick(args)
    if not path:
        where = transcripts_dir()
        if not os.path.isdir(where):
            sys.exit(f'No transcripts at {where}: no session has run here, or this agent keeps them '
                     'elsewhere. Work from the conversation instead.')
        sys.exit(f'No session found for: {" ".join(args) or "the newest"}')
    print(f'# {describe(path)}')
    print(f'# {path}')
    for out in timeline(path):
        print(out)


if __name__ == '__main__':
    try:
        main()
        sys.stdout.flush()
    except BrokenPipeError:
        # Read through `head`: the reader left early, and that is not an error.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
