import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

parser = argparse.ArgumentParser(description="Register all repository footprints. Close KiCad before applying changes.")
parser.add_argument('mode', choices=('setup', 'teardown'))
parser.add_argument('root', type=Path)
parser.add_argument('--library-name', nargs=2, action='append', default=[], metavar=('DIRECTORY', 'NICKNAME'))
parser.add_argument('--config-dir', type=Path, help='KiCad version configuration directory (default: Flatpak 10.0)')
parser.add_argument('--dry-run', action='store_true', help='report changes without writing files')
args = parser.parse_args()
root = args.root.resolve()

config = (args.config_dir or Path.home()/'.var/app/org.kicad.KiCad/config/kicad/10.0').expanduser().resolve()


def fail(message):
    raise ValueError(message)


class Node:
    def __init__(self, start, end, value):
        self.start, self.end, self.value = start, end, value


def parse(text):
    """Parse lists and quoted atoms, retaining spans to preserve untouched settings."""
    tokens = list(re.finditer(r'\s+|;[^\n]*|[()]|"(?:\\.|[^"\\])*"|[^\s()";]+', text))
    pos = 0
    useful = []
    for token in tokens:
        if token.start() != pos:
            fail('Invalid token in fp-lib-table')
        pos = token.end()
        if not token[0].isspace() and not token[0].startswith(';'):
            useful.append(token)
    if pos != len(text):
        fail('Invalid trailing text in fp-lib-table')
    cursor = 0

    def read():
        nonlocal cursor
        if cursor >= len(useful):
            fail('Unclosed list in fp-lib-table')
        token = useful[cursor]
        cursor += 1
        if token[0] == '(':
            children = []
            while cursor < len(useful) and useful[cursor][0] != ')':
                children.append(read())
            if cursor >= len(useful):
                fail('Unclosed list in fp-lib-table')
            end = useful[cursor].end()
            cursor += 1
            return Node(token.start(), end, children)
        if token[0] == ')':
            fail('Unexpected closing parenthesis in fp-lib-table')
        value = token[0]
        if value.startswith('"'):
            value = re.sub(r'\\(.)', r'\1', value[1:-1])
        return Node(token.start(), token.end(), value)

    result = read()
    if cursor != len(useful) or not isinstance(result.value, list) or not result.value or result.value[0].value != 'fp_lib_table':
        fail('Expected a single fp_lib_table expression')
    return result


def fields(node):
    result = {}
    for child in node.value[1:]:
        if not isinstance(child.value, list) or not child.value:
            fail('Malformed library field')
        key = child.value[0].value
        if key in result:
            fail(f'Duplicate library field: {key}')
        result[key] = child
    for key in ('name', 'uri', 'type'):
        if key not in result or len(result[key].value) != 2 or not isinstance(result[key].value[1].value, str):
            fail(f'Missing or invalid library {key}')
    return result


def quote(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def directory(uri, variables):
    for _ in range(20):
        expanded = re.sub(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z_0-9]*)',
                          lambda m: str(variables.get(m[1] or m[2], m[0])), uri)
        if expanded == uri:
            break
        uri = expanded
    if '$' in uri or '://' in uri:
        return None
    path = Path(uri).expanduser()
    # Relative global library paths have no reliable project base.
    return path.resolve() if path.is_absolute() else None


def save(path, content):
    if path.exists():
        suffix = '.backup-before-custom-libs' if args.mode == 'setup' else '.backup-before-custom-libs-teardown'
        backup = path.with_name(path.name + suffix)
        if not backup.exists():
            shutil.copy2(path, backup)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    try:
        if path.exists():
            shutil.copymode(path, temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    names_path = root/'library-names.json'
    library_names = json.loads(names_path.read_text(encoding='utf-8-sig'))
    if not isinstance(library_names, dict) or not all(
        isinstance(key, str) and isinstance(value, str) and value.strip()
        for key, value in library_names.items()
    ):
        fail('library-names.json must map directory names to nonempty nickname strings')
    library_names.update(args.library_name)
    libraries = sorted(p for p in root.glob('*.pretty') if p.is_dir())
    if not libraries:
        fail(f'No .pretty directories found in {root}')
    common_path, table_path = config/'kicad_common.json', config/'fp-lib-table'
    old_common = common_path.read_text(encoding='utf-8-sig') if common_path.exists() else None
    common = json.loads(old_common) if old_common is not None else {}
    original = copy.deepcopy(common)
    environment = common.setdefault('environment', {})
    if environment.get('vars') is None:
        environment['vars'] = {}
    variables = environment['vars']
    before = dict(os.environ)
    before.update(variables)
    override = os.environ.get('MY_KICAD_LIBS')
    if override and directory(override, before) != root:
        fail('Shell MY_KICAD_LIBS points elsewhere; unset it or point it to this footprints directory')
    if args.mode == 'setup':
        variables['MY_KICAD_LIBS'] = str(root)
    after = dict(os.environ)
    after.update(variables)
    old_table = table_path.read_text(encoding='utf-8-sig') if table_path.exists() else '(fp_lib_table\n  (version 7)\n)\n'
    tree = parse(old_table)
    entries = []
    for node in tree.value[1:]:
        if isinstance(node.value, list) and node.value and node.value[0].value == 'lib':
            fs = fields(node)
            uri = fs['uri'].value[1].value
            entries.append((node, fs, directory(uri, before), directory(uri, after)))
    edits, additions = [], []
    kept_names = {}
    for library in libraries:
        target = library.resolve()
        preferred = library_names.get(library.name, library.stem)
        if not preferred.strip() or any(ord(c) < 32 for c in preferred):
            fail(f'Invalid nickname for {library.name}')
        matches = [e for e in entries if target in e[2:]]
        if args.mode == 'teardown':
            for node, fs, _, _ in matches:
                edits.append((node.start, node.end, ''))
                print(f'Remove library: {fs["name"].value[1].value} -> {library.name}')
            continue
        # Prefer the configured nickname when multiple aliases exist.
        matches.sort(key=lambda e: e[1]['name'].value[1].value != preferred)
        uri = '${MY_KICAD_LIBS}/' + library.name
        if matches:
            node, fs, _, _ = matches[0]
            name = fs['name'].value[1].value
            if fs['type'].value[1].value != 'KiCad':
                fail(f'{name}: existing entry has a non-KiCad type')
            def values(node):
                return [values(child) for child in node.value] if isinstance(node.value, list) else node.value

            def settings(fields_):
                return {k: values(v) for k, v in fields_.items() if k not in ('name', 'uri')}
            for duplicate, dup_fields, _, _ in matches[1:]:
                if settings(fs) != settings(dup_fields):
                    fail(f'{library.name}: duplicate aliases have different settings; reconcile them first')
                edits.append((duplicate.start, duplicate.end, ''))
                print(f'Remove duplicate directory alias: {dup_fields["name"].value[1].value} -> {name}')
            atom = fs['uri'].value[1]
            if atom.value != uri:
                edits.append((atom.start, atom.end, quote(uri)))
                print(f'Update path: {name} -> {uri}')
            else:
                print(f'Already configured: {name}')
        else:
            name = preferred
            additions.append(f'  (lib (name {quote(name)}) (type "KiCad") (uri {quote(uri)}) (options "") (descr ""))\n')
            print(f'Add library: {name} -> {uri}')
        if name in kept_names:
            fail(f'Library nickname conflict: {name}')
        kept_names[name] = target
    for _, fs, old_dir, new_dir in entries:
        name = fs['name'].value[1].value
        if name in kept_names and kept_names[name] not in (old_dir, new_dir):
            fail(f'Nickname {name!r} already refers to another directory; no files changed')
    if additions:
        edits.append((tree.end - 1, tree.end - 1, ''.join(additions)))
    new_table = old_table
    for start, end, replacement in sorted(edits, reverse=True):
        new_table = new_table[:start] + replacement + new_table[end:]
    # Audit the complete resulting table, including unrelated existing duplicates.
    seen_names, seen_dirs = set(), {}
    for node in parse(new_table).value[1:]:
        if not isinstance(node.value, list) or not node.value or node.value[0].value != 'lib':
            continue
        fs = fields(node)
        name = fs['name'].value[1].value
        if name in seen_names:
            fail(f'Duplicate nickname in resulting table: {name}')
        seen_names.add(name)
        resolved = directory(fs['uri'].value[1].value, after)
        if resolved is not None:
            if resolved in seen_dirs:
                print(f'Existing unrelated duplicate directory: {seen_dirs[resolved]}, {name} -> {resolved} (unchanged)')
            seen_dirs[resolved] = name
    changes = []
    if args.mode == 'setup' and common != original:
        changes.append((common_path, json.dumps(common, indent=2) + '\n'))
    if new_table != old_table or (args.mode == 'setup' and not table_path.exists()):
        changes.append((table_path, new_table))
    print(f'Configuration: {config}')
    for path, _ in changes:
        print(f'{"Would update" if args.dry_run else "Update"}: {path.name}')
    if not args.dry_run and changes:
        config.mkdir(parents=True, exist_ok=True)
        for path, content in changes:
            save(path, content)
    print('No changes needed.' if not changes else 'Dry run complete.' if args.dry_run else f'{args.mode.capitalize()} complete.')


try:
    main()
except (ValueError, OSError, TypeError, AttributeError) as exc:
    sys.exit(f'ERROR: {exc}')
