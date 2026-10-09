#!/usr/bin/env python3
"""Backport mlx-audio#914's bounded repetition history into a copied app.

Requires Python 3.12 (the same bytecode format as Voicebox 0.5.0).
Does not change the installed app or any user data.
"""
import argparse
import ast
import hashlib
import json
import marshal
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import sys
import types
import zlib

MAGIC = b'MEI\x0c\x0b\x0a\x0b\x0e'
COOKIE = '!8sIIII64s'
TOC = '!IIIIBc'
MODULE = 'mlx_audio.tts.models.qwen3_tts.qwen3_tts'
SOURCE = 'mlx_audio/tts/models/qwen3_tts/qwen3_tts.py'
WINDOW = 64


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive(blob):
    cookie_at = blob.rfind(MAGIC)
    if cookie_at < 0:
        raise ValueError('Not a PyInstaller archive')
    cookie = struct.unpack(COOKIE, blob[cookie_at:cookie_at + 88])
    _, length, toc_offset, toc_length, pyvers, _ = cookie
    if pyvers != 312:
        raise ValueError(f'Expected Python 3.12 archive, got {pyvers}')
    start = cookie_at + 88 - length
    entries = []
    pos, end = start + toc_offset, start + toc_offset + toc_length
    while pos < end:
        row_size, offset, size, raw_size, compressed, kind = struct.unpack(TOC, blob[pos:pos+18])
        name_bytes = blob[pos+18:pos+row_size]
        name = name_bytes.rstrip(b'\0').decode()
        entries.append(dict(name=name, name_bytes=name_bytes, row_size=row_size,
                            offset=offset, size=size, raw_size=raw_size,
                            compressed=compressed, kind=kind,
                            data=blob[start+offset:start+offset+size]))
        pos += row_size
    if pos != end:
        raise ValueError('Invalid TOC size')
    return start, cookie_at, cookie, entries


def unpack(entry):
    return zlib.decompress(entry['data']) if entry['compressed'] else entry['data']


def find_code(code, name):
    if code.co_name == name:
        return code
    for child in code.co_consts:
        if isinstance(child, types.CodeType):
            result = find_code(child, name)
            if result is not None:
                return result
    return None


def replace_functions(code, replacements):
    if code.co_name in replacements:
        return replacements[code.co_name]
    return code.replace(co_consts=tuple(
        replace_functions(child, replacements) if isinstance(child, types.CodeType) else child
        for child in code.co_consts))


def pyz_patch(data, patched_source):
    if data[:4] != b'PYZ\0':
        raise ValueError('Invalid PYZ header')
    toc_at = struct.unpack('!i', data[8:12])[0]
    toc = marshal.loads(data[toc_at:])
    toc_items = list(toc.items()) if isinstance(toc, dict) else list(toc)
    kind, offset, length = dict(toc_items)[MODULE]
    old_code = marshal.loads(zlib.decompress(data[offset:offset+length]))
    new_module = compile(patched_source, old_code.co_filename, 'exec', dont_inherit=True, optimize=0)
    names = ('_sample_token', '_sample_token_batch')
    replacements = {name: find_code(new_module, name) for name in names}
    for name, replacement in replacements.items():
        original = find_code(old_code, name)
        if original is None or replacement is None:
            raise ValueError(f'Missing sampler {name}')
        if original.co_varnames[:original.co_argcount] != replacement.co_varnames[:replacement.co_argcount]:
            raise ValueError('Unexpected sampler signature change')
        if -WINDOW not in replacement.co_consts:
            raise ValueError('Window not present in compiled sampler')
    fixed_code = replace_functions(old_code, replacements)
    compressed = zlib.compress(marshal.dumps(fixed_code), 9)
    out = bytearray(data[:17])
    new_toc = []
    for name, (kind, offset, length) in toc_items:
        if length == 0:
            new_toc.append((name, (kind, offset, length)))
            continue
        payload = compressed if name == MODULE else data[offset:offset+length]
        new_toc.append((name, (kind, len(out), len(payload))))
        out.extend(payload)
    out[8:12] = struct.pack('!i', len(out))
    out.extend(marshal.dumps(dict(new_toc) if isinstance(toc, dict) else new_toc))
    return bytes(out)


def verify(original, patched, expected_source):
    _, _, _, old_entries = archive(original)
    _, _, _, new_entries = archive(patched)
    old = {e['name']: e for e in old_entries}
    new = {e['name']: e for e in new_entries}
    if list(old) != list(new):
        raise ValueError('Archive entry inventory changed')
    changed = [name for name in old if old[name]['data'] != new[name]['data']]
    pyz_name = next(e['name'] for e in old_entries if e['kind'] == b'z')
    if set(changed) != {SOURCE, pyz_name}:
        raise ValueError(f'Unexpected changed archive entries: {changed}')
    if unpack(new[SOURCE]) != expected_source.encode():
        raise ValueError('Source verification failed')
    def pyz_modules(entry):
        data = unpack(entry)
        toc = dict(marshal.loads(data[struct.unpack('!i', data[8:12])[0]:]))
        return {name: zlib.decompress(data[offset:offset+size]) if size else b''
                for name, (_, offset, size) in toc.items()}
    old_modules = pyz_modules(old[pyz_name])
    new_modules = pyz_modules(new[pyz_name])
    changed_modules = [name for name in old_modules if old_modules[name] != new_modules[name]]
    if changed_modules != [MODULE]:
        raise ValueError(f'Unexpected changed compiled modules: {changed_modules}')
    fixed = marshal.loads(new_modules[MODULE])
    for name in ('_sample_token', '_sample_token_batch'):
        if -WINDOW not in find_code(fixed, name).co_consts:
            raise ValueError('Compiled patch missing')
    return dict(changed_archive_entries=changed, changed_compiled_modules=changed_modules,
                verified_compiled_module_count=len(new_modules))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-app', type=Path, default=Path('/Applications/Voicebox.app'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit('Build with Python 3.12')
    output = args.output.resolve()
    if output.exists():
        raise SystemExit('Output already exists; refusing to overwrite')
    source_app = args.source_app.resolve()
    info = plistlib.loads((source_app/'Contents/Info.plist').read_bytes())
    if info['CFBundleShortVersionString'] != '0.5.0':
        raise SystemExit('This backport is for Voicebox 0.5.0 only')
    binary = (source_app/'Contents/MacOS/voicebox-server').read_bytes()
    start, cookie_at, cookie, entries = archive(binary)
    source_entry = next(e for e in entries if e['name'] == SOURCE)
    source = unpack(source_entry).decode()
    replacements = {
        'unique_tokens = list(set(generated_tokens))': 'unique_tokens = list(set(generated_tokens[-64:]))',
        'unique_tokens = list(set(gen_tokens))': 'unique_tokens = list(set(gen_tokens[-64:]))',
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise ValueError('Source does not match the expected old implementation')
        source = source.replace(old, new)
    ast.parse(source)
    pyz_entry = next(e for e in entries if e['kind'] == b'z')
    payloads = {
        SOURCE: source.encode(),
        pyz_entry['name']: pyz_patch(unpack(pyz_entry), source),
    }
    payload = bytearray()
    new_toc = bytearray()
    for entry in entries:
        data = entry['data']
        raw_size = entry['raw_size']
        if entry['name'] in payloads:
            raw = payloads[entry['name']]
            data = zlib.compress(raw, 9) if entry['compressed'] else raw
            raw_size = len(raw)
        new_toc.extend(struct.pack(TOC, entry['row_size'], len(payload), len(data),
                                   raw_size, entry['compressed'], entry['kind']))
        new_toc.extend(entry['name_bytes'])
        payload.extend(data)
    available = cookie[2]
    if len(payload) > available:
        raise ValueError(f'Patch exceeds the original archive by {len(payload)-available} bytes')
    padding = available - len(payload)
    payload.extend(b'\0' * padding)
    if len(new_toc) != cookie[3]:
        raise ValueError('TOC length changed')
    patched = binary[:start] + payload + new_toc + binary[cookie_at:]
    if len(patched) != len(binary):
        raise ValueError('Mach-O size changed')
    checks = verify(binary, patched, source)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_app, output, symlinks=True)
    (output/'Contents/MacOS/voicebox-server').write_bytes(patched)
    info['CFBundleDisplayName'] = 'Voicebox 节奏修复版'
    info['CFBundleName'] = 'Voicebox 节奏修复版'
    # Keep identifier and version so existing local voices/settings remain available.
    (output/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    manifest = dict(patch='voicebox-0.5.0-pace-fix-1', base_version='0.5.0',
                    engine_version='mlx-audio 0.4.1', window_tokens=WINDOW,
                    upstream='https://github.com/Blaizzy/mlx-audio/pull/914',
                    original_server_sha256=sha(binary), patched_server_before_signing_sha256=sha(patched),
                    patched_source_sha256=sha(source.encode()), padding_bytes=padding, **checks)
    (output/'Contents/Resources/pace-fix-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(output)], check=True)
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(output)], check=True)
    # Signing changes only the signature tail; re-check the actual embedded archive.
    signed_binary = (output/'Contents/MacOS/voicebox-server').read_bytes()
    verify(binary, signed_binary, source)
    manifest['signed_server_sha256'] = sha(signed_binary)
    (output.parent/'build-verification.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (output.parent/'qwen3_tts.patched.py').write_text(source)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
