#!/usr/bin/env python3
"""Run the real old and patched samplers against mlx-audio#914 regression cases."""
import argparse
import json
import marshal
from pathlib import Path
import sys
import types
import zlib
import struct
from build_pace_fix import archive, unpack, MODULE, find_code


def get_module(path):
    _, _, _, entries = archive(Path(path).read_bytes())
    pyz = unpack(next(e for e in entries if e['kind'] == b'z'))
    toc = dict(marshal.loads(pyz[struct.unpack('!i', pyz[8:12])[0]:]))
    _, offset, size = toc[MODULE]
    return marshal.loads(zlib.decompress(pyz[offset:offset+size]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runtime', required=True)
    p.add_argument('--patched-server', required=True)
    p.add_argument('--report', required=True)
    args = p.parse_args()
    sys.path.insert(0, args.runtime)
    import mlx.core as mx
    mx.set_default_device(mx.cpu)
    modules = {
        'original': get_module('/Applications/Voicebox.app/Contents/MacOS/voicebox-server'),
        'patched': get_module(args.patched_server),
    }
    results = []
    histories = {'outside_window': [5] + [0] * 100,
                 'inside_window': [5] * 100,
                 'short_history': [5, 0, 0],
                 'empty_history': []}
    for function_name in ('_sample_token', '_sample_token_batch'):
        for case, history in histories.items():
            observed = {}
            for version, module in modules.items():
                function = types.FunctionType(find_code(module, function_name), {'mx': mx})
                kwargs = dict(temperature=0.0, top_k=0, top_p=1.0,
                              repetition_penalty=1.5, suppress_tokens=None,
                              eos_token_id=None, min_p=0.0)
                if function_name == '_sample_token':
                    kwargs['generated_tokens'] = history
                else:
                    kwargs['generated_tokens_per_seq'] = [history]
                logits = mx.array([[[1., 1., 1., 1., 1., 10., 1., 9.]]], dtype=mx.float32)
                observed[version] = function(None, logits, **kwargs).item()
            expected_old = 5 if case == 'empty_history' else 7
            expected_new = 5 if case in ('outside_window', 'empty_history') else 7
            assert observed == {'original': expected_old, 'patched': expected_new}, (case, observed)
            results.append(dict(function=function_name, case=case, **observed, passed=True))
    report = dict(status='passed', cases=len(results), tests=results,
                  explanation='Old tokens outside the 64-token window no longer receive a penalty; recent repetition remains penalized.')
    Path(args.report).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
