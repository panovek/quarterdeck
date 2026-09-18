#!/usr/bin/env python3
"""Check that a Quarterdeck installation still holds.

    python3 <quarterdeck-setup>/assets/tools/doctor.py [TARGET]

TARGET is the project root; the current directory when omitted. This is the executable half of
the installer: the setup skill decides and writes, `doctor` verifies. It is deliberately the only
part that must be code — a rule that is checked by the same model that applied it is not checked.

What it verifies, in order:

  1. `.quarterdeck.json` parses and carries every field the hook, the checks and the skills read.
  2. Every file Quarterdeck ships unchanged — doctrine, skills, hook, checks, CI — is byte-identical
     to this version's copy. A difference is either a local edit that belongs upstream or an
     outdated install; either way the fix is the setup skill's upgrade mode. A path an earlier
     version installed under another name is reported as stale until it is moved.
  3. Seeded files (logs, ADR seeds, the pull request template) exist. They are never compared.
  4. The two files the setup skill renders — the board procedures and the agent-instruction
     block — exist and state the facts the manifest holds. They are fact-checked, not diffed.
  5. The hook is wired in `.claude/settings.json`, and fires: it is run against commands it must
     refuse and commands it must allow, each with a known answer.
  6. The board and the commands are bound, and the test globs match something.

Exit 0 when nothing failed (warnings allowed), 1 otherwise. Python 3.9+, standard library only.
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.dirname(HERE)
MANIFEST = '.quarterdeck.json'
BEGIN, END = '<!-- quarterdeck:begin -->', '<!-- quarterdeck:end -->'
STATUSES = ['open', 'refine', 'todo', 'in progress', 'in review', 'done', 'closed']
REQUIRED = {
    'quarterdeck': str, 'main_branch': str, 'task_prefix': str, 'docs_dir': str, 'adr_dir': str,
    'domain_doc': str, 'board': dict, 'commands': dict, 'core_dir': str, 'source_dirs': list,
    'test_globs': list, 'import_aliases': dict, 'agent_signature': str, 'ci': bool, 'sources': list,
}


def read(path: str) -> str:
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def version() -> str:
    return read(os.path.join(ASSETS, 'VERSION')).strip()


def static_files(manifest: dict) -> dict:
    """Installed path → shipped path, for every file that must be byte-identical."""
    docs = manifest['docs_dir'].rstrip('/')
    files = {
        f'{docs}/workflow.md': 'doctrine/workflow.md',
        f'{docs}/task-template.md': 'doctrine/task-template.md',
        '.claude/skills/refine/SKILL.md': 'skills/refine/SKILL.md',
        '.claude/skills/implement/SKILL.md': 'skills/implement/SKILL.md',
        '.claude/hooks/guard-main.py': 'hooks/guard-main.py',
        'tools/quarterdeck/check-tests-first.py': 'tools/check-tests-first.py',
        'tools/quarterdeck/check-pr-evidence.py': 'tools/check-pr-evidence.py',
        'tools/quarterdeck/test-only-modules.py': 'tools/test-only-modules.py',
    }
    if manifest.get('ci'):
        files['.github/workflows/quarterdeck.yml'] = 'templates/ci/quarterdeck.yml'
    return files


# Installed path an earlier version used → the path this version installs instead. The upgrade
# mode of the setup skill moves the directory so that a local edit survives the rename.
STALE = {
    '.claude/skills/grill-task/SKILL.md': '.claude/skills/refine/SKILL.md',  # renamed in 0.3.0
}


def seeded_files(manifest: dict) -> list:
    docs, adr = manifest['docs_dir'].rstrip('/'), manifest['adr_dir'].rstrip('/')
    return [f'{docs}/agent-notes.md', f'{adr}/README.md', f'{adr}/adr-template.md',
            '.github/pull_request_template.md']


def hook_exit(target: str, command: str) -> int:
    payload = json.dumps({'tool_name': 'Bash', 'tool_input': {'command': command}})
    env = dict(os.environ, CLAUDE_PROJECT_DIR=os.path.abspath(target))
    result = subprocess.run([sys.executable, os.path.join(target, '.claude', 'hooks', 'guard-main.py')],
                            input=payload, capture_output=True, text=True, env=env, cwd=target)
    return result.returncode


def git(target: str, *args: str) -> str:
    try:
        result = subprocess.run(['git', *args], capture_output=True, text=True, cwd=target, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ''
    return result.stdout.strip() if result.returncode == 0 else ''


class Report:
    def __init__(self):
        self.failures, self.warnings = [], []

    def ok(self, label): print(f'  ok       {label}')

    def fail(self, label): self.failures.append(label); print(f'  FAIL     {label}')

    def warn(self, label): self.warnings.append(label); print(f'  warn     {label}')

    def check(self, condition, label, otherwise=None, severity='fail'):
        if condition:
            self.ok(label)
        else:
            (self.fail if severity == 'fail' else self.warn)(otherwise or label)
        return bool(condition)


def main() -> None:
    parser = argparse.ArgumentParser(prog='doctor.py', description=__doc__.split('\n')[0])
    parser.add_argument('target', nargs='?', default='.')
    target = parser.parse_args().target
    r = Report()
    this = version()
    print(f'quarterdeck doctor {this} · {os.path.abspath(target)}\n')

    # 1. The manifest.
    print('The manifest')
    path = os.path.join(target, MANIFEST)
    if not os.path.isfile(path):
        sys.exit(f'  FAIL     no {MANIFEST} in {os.path.abspath(target)}; run the setup skill first')
    try:
        manifest = json.loads(read(path))
    except ValueError as error:
        sys.exit(f'  FAIL     {MANIFEST} is not valid JSON: {error}')
    for key, kind in REQUIRED.items():
        r.check(isinstance(manifest.get(key), kind), f'{key}', f'{MANIFEST} lacks `{key}` ({kind.__name__})')
    if r.failures:
        print(f'\n{len(r.failures)} failure(s) in the manifest; nothing else can be checked')
        sys.exit(1)
    board, commands = manifest['board'], manifest['commands']
    for key in ('kind', 'name', 'statuses', 'lists'):
        r.check(key in board, f'board.{key}', f'{MANIFEST} lacks `board.{key}`')
    r.check(set(board.get('statuses', {})) == set(STATUSES), 'board.statuses maps all seven statuses',
            f'board.statuses must map exactly: {", ".join(STATUSES)}')
    for key in ('check', 'test', 'mutation', 'arch'):
        r.check(key in commands, f'commands.{key}', f'{MANIFEST} lacks `commands.{key}` (empty string when none)')
    r.check(manifest['quarterdeck'] == this, f'installed by quarterdeck {manifest["quarterdeck"]}',
            f'installed by quarterdeck {manifest["quarterdeck"]}, this is {this}; run the setup skill in upgrade mode',
            severity='warn')

    # 2. Files that must be identical to what ships.
    print('\nShipped files')
    for installed, shipped in static_files(manifest).items():
        full = os.path.join(target, installed)
        if not os.path.isfile(full):
            r.fail(f'{installed} is missing')
        elif read(full) != read(os.path.join(ASSETS, shipped)):
            r.fail(f'{installed} differs from quarterdeck {this} — outdated, or a local edit that belongs upstream')
        else:
            r.ok(installed)
    for old, new in STALE.items():
        if os.path.isfile(os.path.join(target, old)):
            r.fail(f'{old} is stale: quarterdeck {this} installs it as {new}; move the directory (upgrade mode) and delete the old one')
    for name in ('check-tests-first.py', 'check-pr-evidence.py', 'test-only-modules.py'):
        full = os.path.join(target, 'tools', 'quarterdeck', name)
        if os.path.isfile(full) and not os.access(full, os.X_OK):
            r.warn(f'tools/quarterdeck/{name} is not executable (chmod +x)')

    # 3. Seeds.
    print('\nSeeded files')
    for rel in seeded_files(manifest):
        r.check(os.path.isfile(os.path.join(target, rel)), rel, f'{rel} is missing; the setup skill seeds it', severity='warn')

    # 4. Rendered files: fact-checked.
    print('\nRendered files')
    docs = manifest['docs_dir'].rstrip('/')
    board_file = os.path.join(target, docs, 'board.md')
    if r.check(os.path.isfile(board_file), f'{docs}/board.md exists', f'{docs}/board.md is missing'):
        text = read(board_file)
        missing = [name for name in board['statuses'].values() if name not in text]
        r.check(not missing, f'{docs}/board.md names every board status',
                f'{docs}/board.md does not mention board status(es): {", ".join(missing)}')
        missing = [name for name in board['lists'] if name not in text]
        r.check(not missing, f'{docs}/board.md names every agent-writable list',
                f'{docs}/board.md does not mention list(s): {", ".join(missing)}')

    carriers = [n for n in ('CLAUDE.md', 'AGENTS.md') if os.path.isfile(os.path.join(target, n))]
    blocks = {n: read(os.path.join(target, n)) for n in carriers}
    blocks = {n: t for n, t in blocks.items() if BEGIN in t and END in t}
    if r.check(bool(blocks), f'{" and ".join(blocks) or "CLAUDE.md / AGENTS.md"} carries the quarterdeck block',
               'neither CLAUDE.md nor AGENTS.md carries the quarterdeck block'):
        for name, text in blocks.items():
            r.check(text.count(BEGIN) == 1 and text.count(END) == 1 and text.index(BEGIN) < text.index(END),
                    f'{name}: one block, well-formed', f'{name}: the block markers are duplicated or reversed')
            block = text[text.index(BEGIN):text.index(END)]
            facts = {
                'the check command': commands['check'],
                'the main branch': manifest['main_branch'],
                'the task prefix': manifest['task_prefix'],
                'the board name': board['name'],
                'the board file': f'{docs}/board.md',
                'the workflow document': f'{docs}/workflow.md',
                'the task template': f'{docs}/task-template.md',
                'the ADR directory': manifest['adr_dir'].rstrip('/'),
            }
            if commands.get('mutation'):
                facts['the mutation command'] = commands['mutation']
            for row in manifest['sources']:
                facts[f'the owner of "{row.get("domain", "?")}"'] = row.get('owner', '')
            for label, value in facts.items():
                r.check(bool(value) and value in block, f'{name}: states {label}',
                        f'{name}: the block does not state {label} ({value!r}); re-render it from templates/claude-block.md')
            r.check('| The code |' in block, f'{name}: the sources table ends with the code row',
                    f'{name}: the sources table must end with the row "What currently exists | The code | …"')

    # 5. The hook.
    print('\nThe hook')
    settings = os.path.join(target, '.claude', 'settings.json')
    wired = False
    if os.path.isfile(settings):
        try:
            for entry in json.loads(read(settings)).get('hooks', {}).get('PreToolUse', []):
                wired = wired or any('guard-main.py' in h.get('command', '') for h in entry.get('hooks', []))
        except ValueError:
            r.fail('.claude/settings.json is not valid JSON')
    r.check(wired, '.claude/settings.json wires guard-main.py as a PreToolUse hook',
            '.claude/settings.json does not wire guard-main.py as a PreToolUse hook')
    main, prefix = manifest['main_branch'], manifest['task_prefix']
    on_main = git(target, 'rev-parse', '--abbrev-ref', 'HEAD') == main
    cases = [
        (f'git push origin {main}', 2), ('git push --force origin whatever', 2), ('git merge feature', 2),
        ('git rebase -i HEAD~3', 2), ('gh pr merge 12', 2),
        (f'git switch {prefix}abc-slug && git push -u origin {prefix}abc-slug', 0),
        (f'git switch {prefix}abc-slug && git commit -m "Add tests"', 0),
        ('git commit -m "Add tests"', 2 if on_main else 0),
        ('git status', 0), (f"cat <<'EOF'\nnever run git rebase on {main}\nEOF", 0),
    ]
    if os.path.isfile(os.path.join(target, '.claude', 'hooks', 'guard-main.py')):
        for command, expected in cases:
            got = hook_exit(target, command)
            label = f'{"refuses" if expected else "allows "} {command.splitlines()[0]!r}'
            r.check(got == expected, label, f'{label} — exit {got}, expected {expected}')

    # 6. Bindings.
    print('\nThe board and the commands')
    r.ok(f'board: {board["kind"]} ({board["name"]}); agents may create in {", ".join(board["lists"])}')
    if board['kind'] == 'github' and not shutil.which('gh'):
        r.warn('board is GitHub Issues but `gh` is not on PATH')
    for key in ('check', 'test'):
        r.check(bool(commands.get(key)), f'{key} command: {commands.get(key)}', f'{key} command is empty')
    r.check(bool(commands.get('mutation')), f'mutation command: {commands.get("mutation")}',
            'no mutation command: failure mode 4 rests on the tests-first check and the prose ban alone', severity='warn')
    matched = any(glob.glob(os.path.join(target, g), recursive=True) for g in manifest['test_globs'])
    r.check(matched, f'test globs match existing files: {", ".join(manifest["test_globs"])}',
            f'no file matches any test glob ({", ".join(manifest["test_globs"])}); the tests-first and test-only-module checks would misfire',
            severity='warn')
    r.check('test-only-modules' in commands.get('check', ''), 'test-only-module check is in the check chain',
            'test-only-module check is not in the check chain yet (README, step 3)', severity='warn')
    no_domain = manifest['domain_doc'] in ('', 'none yet') or any('none yet' in row.get('owner', '') for row in manifest['sources'])
    if no_domain:
        r.warn('no domain document owns intent: the citation rule has nothing to cite but ADRs and tasks')
    elif not os.path.exists(os.path.join(target, manifest['domain_doc'])):
        r.warn(f'domain document `{manifest["domain_doc"]}` does not exist at that path')

    print('\nReadiness, by failure mode')
    readiness = {
        '1 · undecided ground': 'definition of ready and tier-3 stop — prose in the skills' + ('; no domain document yet' if no_domain else ''),
        '2 · losing the thread': f'ADRs in {manifest["adr_dir"]}, evidence block check, ' + ('architecture command set' if commands.get('arch') else 'no architecture record'),
        '3 · invented work': 'test-only-module check ' + ('in the check chain' if 'test-only-modules' in commands.get('check', '') else 'installed but NOT in the check chain'),
        '4 · tests that prove nothing': 'tests-first check' + (', mutation gate' if commands.get('mutation') else ', no mutation gate') + (' — in CI' if manifest.get('ci') else ' — no CI workflow'),
        '5 · blocked, improvising': 'retry budget and waiting_on pre-flight — prose in the skills; the hook refuses the merge',
    }
    for mode, answer in readiness.items():
        print(f'  {mode:34} {answer}')

    print(f'\n{len(r.failures)} failure(s), {len(r.warnings)} warning(s)')
    sys.exit(1 if r.failures else 0)


if __name__ == '__main__':
    main()
