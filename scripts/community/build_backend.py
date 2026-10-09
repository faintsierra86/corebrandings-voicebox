"""Rebuild Voicebox's Python application atop its original bundled runtime.

Python 3.12 only. Preserve native dependencies byte-for-byte after decompression,
replace the entire backend with the pinned upstream source, and retain pace fix.
"""
import argparse
import hashlib
import json
import marshal
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pace_fix import archive, unpack, pyz_patch, COOKIE, TOC, MODULE, SOURCE


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--original', type=Path, default=Path('/Applications/Voicebox.app/Contents/MacOS/voicebox-server'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--runtime', type=Path)
    args = p.parse_args()
    assert sys.version_info[:2] == (3, 12)
    original = args.original.read_bytes()
    expected = 'c8e7fd28b0177ad2c0bd9feb8de5f5415f73fbf3588afedd0f03a0621263967a'
    assert digest(original) == expected, 'Original bundled runtime differs from the verified input'
    start, cookie_at, cookie, entries = archive(original)
    pyz_entry = next(e for e in entries if e['kind'] == b'z')
    qwen_source = unpack(next(e for e in entries if e['name'] == SOURCE)).decode()
    for old, new in [('list(set(generated_tokens))', 'list(set(generated_tokens[-64:]))'),
                     ('list(set(gen_tokens))', 'list(set(gen_tokens[-64:]))')]:
        assert qwen_source.count(old) == 1
        qwen_source = qwen_source.replace(old, new)
    pyz = pyz_patch(unpack(pyz_entry), qwen_source)
    toc = dict(marshal.loads(pyz[struct.unpack('!i', pyz[8:12])[0]:]))
    modules = {n: (kind, pyz[offset:offset+size]) for n, (kind, offset, size) in toc.items()}
    replaced = {}
    for path in sorted((args.repo / 'backend').rglob('*.py')):
        relative = path.relative_to(args.repo)
        if 'tests' in relative.parts or '__pycache__' in relative.parts:
            continue
        if path.name.startswith(('build_', 'pyi_rth_')):
            continue
        name = '.'.join(relative.with_suffix('').parts)
        is_package = path.name == '__init__.py'
        if is_package:
            name = name.removesuffix('.__init__')
        source = path.read_bytes()
        code = compile(source, str(relative), 'exec', dont_inherit=True, optimize=0)
        modules[name] = (int(is_package), zlib.compress(marshal.dumps(code), 9))
        replaced[name] = digest(source)
    out = bytearray(pyz[:17])
    new_toc = {}
    pyz_compression_saved = 0
    for name, (kind, payload) in modules.items():
        if payload:
            candidate = zlib.compress(zlib.decompress(payload), 9)
            if len(candidate) < len(payload):
                pyz_compression_saved += len(payload) - len(candidate)
                payload = candidate
        new_toc[name] = (kind, len(out), len(payload))
        out.extend(payload)
    out[8:12] = struct.pack('!i', len(out))
    out.extend(marshal.dumps(new_toc))
    raw_replacements = {pyz_entry['name']: bytes(out), SOURCE: qwen_source.encode(),
                        'server': marshal.dumps(compile((args.repo/'backend/server.py').read_bytes(),
                                                        'backend/server.py', 'exec', dont_inherit=True))}
    hook = args.repo/'backend/pyi_rth_numpy_compat.py'
    raw_replacements['pyi_rth_numpy_compat'] = marshal.dumps(compile(
        hook.read_bytes(), 'backend/pyi_rth_numpy_compat.py', 'exec', dont_inherit=True))
    payload = bytearray()
    toc_out = bytearray()
    compressed_unchanged = []
    for e in entries:
        raw_size, data = e['raw_size'], e['data']
        if e['name'] in raw_replacements:
            raw = raw_replacements[e['name']]
            data = zlib.compress(raw, 9) if e['compressed'] else raw
            raw_size = len(raw)
        elif e['name'] in ('torch/lib/libtorch_cpu.dylib', 'mlx/lib/mlx.metallib',
                           'llvmlite/binding/libllvmlite.dylib'):
            # Compression-only change provides space while keeping Mach-O offsets.
            raw = unpack(e)
            candidate = zlib.compress(raw, 9)
            if len(candidate) < len(data):
                data = candidate
                compressed_unchanged.append(e['name'])
        toc_out.extend(struct.pack(TOC, e['row_size'], len(payload), len(data),
                                   raw_size, e['compressed'], e['kind']))
        toc_out.extend(e['name_bytes'])
        payload.extend(data)
    padding = cookie[2] - len(payload)
    assert padding >= 0, f'Archive exceeds space by {-padding} bytes'
    payload.extend(b'\0' * padding)
    assert len(toc_out) == cookie[3]
    patched = original[:start] + payload + toc_out + original[cookie_at:]
    assert len(patched) == len(original)
    _, _, _, check_entries = archive(patched)
    assert [e['name'] for e in entries] == [e['name'] for e in check_entries]
    for old, new in zip(entries, check_entries):
        if old['name'] in raw_replacements:
            assert unpack(new) == raw_replacements[old['name']]
        else:
            assert unpack(old) == unpack(new), old['name']
    # Check all non-backend dependencies remain exactly the original code.
    original_pyz = unpack(pyz_entry)
    original_toc = dict(marshal.loads(original_pyz[struct.unpack('!i', original_pyz[8:12])[0]:]))
    for name, (kind, offset, size) in original_toc.items():
        if name.startswith('backend') or name == MODULE:
            continue
        assert modules[name] == (kind, original_pyz[offset:offset+size]), name
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    args.output.chmod(0o755)
    report = {'runtime_base': 'Voicebox 0.5.0 Apple Silicon',
              'backend_source_commit': 'a00d271', 'backend_modules': replaced,
              'numpy_compat_hook_source_commit': '82caf7d',
              'qwen_repetition_window': 64, 'native_dependencies_unchanged': True,
              'compression_only_entries': compressed_unchanged, 'padding_bytes': padding,
              'pyz_compression_saved_bytes': pyz_compression_saved,
              'server_sha256_before_signing': digest(patched)}
    args.output.with_suffix('.verification.json').write_text(json.dumps(report, indent=2)+'\n')
    if args.runtime:
        args.runtime.mkdir(parents=True, exist_ok=True)
        for e in check_entries:
            if e['kind'] in (b'b', b'x'):
                target = args.runtime/e['name']
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(unpack(e))
            elif e['kind'] == b'n':
                target = args.runtime/e['name']
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.is_symlink():
                    target.symlink_to(unpack(e).rstrip(b'\0').decode())
        import importlib.util
        for name, (kind, packed) in modules.items():
            if not packed:
                continue
            target = args.runtime / (name.replace('.', '/') + ('/__init__.pyc' if kind == 1 else '.pyc'))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(importlib.util.MAGIC_NUMBER + b'\0'*12 + zlib.decompress(packed))
    print(json.dumps({k: v for k, v in report.items() if k != 'backend_modules'}, indent=2))


if __name__ == '__main__':
    main()
