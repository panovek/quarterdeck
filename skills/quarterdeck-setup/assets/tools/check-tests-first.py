#!/usr/bin/env python3
"""The first commit on a task branch contains test files only, and nothing else.

Workflow section 3 of `/implement`: that commit is the evidence that the tests were written
against the specification rather than against the implementation. This check reads the branch
history and refuses a pull request whose first commit touches anything that is not a test file.

Test files are the paths matching `test_globs` in `.quarterdeck.json`. Run from the repository
root, on a pull request:

    python3 tools/quarterdeck/check-tests-first.py --base origin/main

With `--run "<test command>"` the check also checks out that first commit in a temporary
worktree and requires the test command to fail there — the "and they fail" half of the rule. It
is optional because a fresh worktree needs the project's dependencies installed.

Exit 0 when the rule holds, 1 when it does not, 2 when the check could not run.
"""

import argparse
import fnmatch
import json
import os
import subprocess
import sys
import tempfile


def git(*args: str, cwd: str = '.') -> str:
    result = subprocess.run(['git', *args], capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f'git {" ".join(args)} failed: {result.stderr.strip()}', file=sys.stderr)
        sys.exit(2)
    return result.stdout


def load_globs(manifest: str) -> list:
    try:
        with open(manifest, encoding='utf-8') as handle:
            globs = json.load(handle).get('test_globs') or []
    except (OSError, ValueError) as error:
        print(f'cannot read {manifest}: {error}', file=sys.stderr)
        sys.exit(2)
    if not globs:
        print(f'{manifest} has no test_globs; the check cannot tell a test from a source file', file=sys.stderr)
        sys.exit(2)
    return globs


def is_test(path: str, globs: list) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in globs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--base', required=True, help='the main branch, e.g. origin/main')
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--manifest', default='.quarterdeck.json')
    parser.add_argument('--run', metavar='COMMAND', help='test command that must fail at the first commit')
    args = parser.parse_args()

    globs = load_globs(args.manifest)
    commits = git('rev-list', '--reverse', f'{args.base}..{args.head}').split()
    if not commits:
        print(f'no commits between {args.base} and {args.head}; nothing to check')
        sys.exit(0)
    first = commits[0]
    files = git('diff-tree', '--no-commit-id', '--name-only', '-r', first).split()
    subject = git('log', '-1', '--format=%s', first).strip()

    offenders = [path for path in files if not is_test(path, globs)]
    if not files:
        print(f'first commit {first[:10]} "{subject}" changes no files')
        sys.exit(1)
    if offenders:
        print(f'first commit {first[:10]} "{subject}" touches files that are not tests:')
        for path in offenders:
            print(f'  {path}')
        print(f'test files are those matching: {", ".join(globs)}')
        sys.exit(1)
    print(f'first commit {first[:10]} "{subject}" is tests only: {len(files)} file(s)')

    if args.run:
        with tempfile.TemporaryDirectory() as tree:
            git('worktree', 'add', '--detach', tree, first)
            try:
                result = subprocess.run(args.run, shell=True, cwd=tree, capture_output=True, text=True)
            finally:
                git('worktree', 'remove', '--force', tree)
        if result.returncode == 0:
            print(f'the tests pass at {first[:10]}; they were meant to fail before the implementation existed')
            sys.exit(1)
        print(f'the tests fail at {first[:10]}, as they should (exit {result.returncode})')
    sys.exit(0)


if __name__ == '__main__':
    os.chdir(os.environ.get('QUARTERDECK_ROOT') or '.')
    main()
