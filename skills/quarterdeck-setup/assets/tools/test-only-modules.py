#!/usr/bin/env python3
"""No module exists only to be tested.

Code written so that there is something to test is still code nobody asked for. The rule says it
plainly — if the only caller of a thing is its own test, the thing is deleted, not tested — and
this is that rule made executable. Dead-code tools do not catch it: a module imported by its own
test is "used" as far as they are concerned.

The check is narrow on purpose. A module with no importer at all is not a violation — a project
may legitimately build a layer before the layer that consumes it, and dead-code tools report that
separately. What is caught is the shape that only invented work takes: a module that something
imports, where everything importing it is a test.

Reads `source_dirs`, `test_globs` and `import_aliases` from `.quarterdeck.json`. Understands
TypeScript / JavaScript (`import … from`, `export … from`, `require()`, relative paths and the
aliases) and Python (`import a.b`, `from a.b import`, relative `from .x import`). Other languages
are not scanned; the project's own equivalent goes into the check chain instead.

    python3 tools/quarterdeck/test-only-modules.py

Exit 0 when nothing is imported only by tests, 1 when something is, 2 when the scan resolved no
imports at all — a guard that silently stopped resolving would otherwise pass for the wrong reason.
"""

import argparse
import fnmatch
import json
import os
import re
import sys

JS_EXT = ('.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs')
PY_EXT = ('.py',)
JS_SPECIFIER = re.compile(r'''(?:^|\n)\s*(?:import|export)\b[^'"\n]*?from\s*['"]([^'"]+)['"]|(?:^|\n)\s*import\s*['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]\s*\)''')
PY_FROM = re.compile(r'^\s*from\s+([.\w]+)\s+import\b', re.M)
PY_IMPORT = re.compile(r'^\s*import\s+([\w.]+(?:\s*,\s*[\w.]+)*)', re.M)


def load_manifest(path: str) -> dict:
    try:
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError) as error:
        print(f'cannot read {path}: {error}', file=sys.stderr)
        sys.exit(2)


def walk(dirs: list) -> list:
    files = []
    for root_dir in dirs:
        for root, _, names in os.walk(root_dir):
            if 'node_modules' in root.split(os.sep) or '__pycache__' in root:
                continue
            for name in names:
                if name.endswith(JS_EXT + PY_EXT):
                    files.append(os.path.normpath(os.path.join(root, name)))
    return files


def exists(path: str) -> bool:
    return os.path.isfile(path)


def resolve_js(base: str) -> str:
    """A specifier without extension, or with the `.js` that ESM TypeScript writes for a `.ts` file."""
    stem = re.sub(r'\.(js|mjs|cjs|jsx)$', '', base)
    candidates = [base] + [stem + ext for ext in JS_EXT] + [os.path.join(stem, 'index' + ext) for ext in JS_EXT]
    for candidate in candidates:
        if exists(candidate):
            return os.path.normpath(candidate)
    return None


def js_targets(file: str, source: str, aliases: dict) -> list:
    targets = []
    for match in JS_SPECIFIER.finditer(source):
        specifier = next(group for group in match.groups() if group)
        alias = next(((prefix, directory) for prefix, directory in aliases.items() if specifier.startswith(prefix)), None)
        if alias:
            target = resolve_js(os.path.join(alias[1], specifier[len(alias[0]):]))
        elif specifier.startswith('.'):
            target = resolve_js(os.path.join(os.path.dirname(file), specifier))
        else:
            continue
        if target:
            targets.append(target)
    return targets


def resolve_py(parts: list, roots: list) -> str:
    for root in roots:
        base = os.path.join(root, *parts) if parts else root
        for candidate in (base + '.py', os.path.join(base, '__init__.py')):
            if exists(candidate):
                return os.path.normpath(candidate)
    return None


def py_targets(file: str, source: str, roots: list) -> list:
    targets = []
    for match in PY_FROM.finditer(source):
        module = match.group(1)
        dots = len(module) - len(module.lstrip('.'))
        parts = [part for part in module.lstrip('.').split('.') if part]
        if dots:
            here = os.path.dirname(file)
            for _ in range(dots - 1):
                here = os.path.dirname(here)
            target = resolve_py(parts, [here])
        else:
            target = resolve_py(parts, roots)
        if target:
            targets.append(target)
    for match in PY_IMPORT.finditer(source):
        for module in re.split(r'\s*,\s*', match.group(1)):
            target = resolve_py(module.split('.'), roots)
            if target:
                targets.append(target)
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--manifest', default='.quarterdeck.json')
    parser.add_argument('--verbose', action='store_true', help='print every resolved import')
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    source_dirs = manifest.get('source_dirs') or ['src']
    test_globs = manifest.get('test_globs') or []
    aliases = manifest.get('import_aliases') or {}
    if not test_globs:
        print('the manifest has no test_globs; the check cannot tell a test from a source file', file=sys.stderr)
        sys.exit(2)

    # Tests often live outside the source directories (`tests/`, `spec/`): walk the literal
    # directory each test glob starts with as well, or the importers are never seen.
    test_dirs = [g.split('*')[0].rstrip('/') for g in test_globs if not g.startswith('*') and '/' in g]
    scan_dirs = list(dict.fromkeys(d for d in source_dirs + test_dirs if d and os.path.isdir(d)))
    files = walk(scan_dirs)
    py_roots = ['.'] + source_dirs
    importers = {}
    resolved = 0
    for file in files:
        with open(file, encoding='utf-8', errors='replace') as handle:
            source = handle.read()
        targets = js_targets(file, source, aliases) if file.endswith(JS_EXT) else py_targets(file, source, py_roots)
        for target in targets:
            if target == file:
                continue
            resolved += 1
            importers.setdefault(target, set()).add(file)
            if args.verbose:
                print(f'{file} -> {target}')

    def is_test(path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in test_globs)

    if files and resolved == 0:
        print(f'scanned {len(files)} files under {", ".join(source_dirs)} and resolved no imports; '
              'check source_dirs and import_aliases in the manifest', file=sys.stderr)
        sys.exit(2)

    test_only = sorted(
        (target, sorted(sources)) for target, sources in importers.items()
        if not is_test(target) and all(is_test(source) for source in sources)
    )
    if test_only:
        print('modules that exist only to be tested:')
        for target, sources in test_only:
            print(f'  {target} — imported only by {", ".join(sources)}')
        sys.exit(1)
    print(f'no module is imported only by tests ({len(files)} files, {resolved} imports resolved)')
    sys.exit(0)


if __name__ == '__main__':
    main()
