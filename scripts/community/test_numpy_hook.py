"""Exercise the exact frozen hook's import gate and ABI fallback."""
import json
import builtins
import marshal
from pathlib import Path
import sys
from types import FunctionType, SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pace_fix import archive, unpack, find_code
import numpy as np
import torch

binary = Path(sys.argv[1]).read_bytes()
_, _, _, entries = archive(binary)
code = marshal.loads(unpack(next(e for e in entries if e['name']=='pyi_rth_numpy_compat')))
function_code = find_code(code, '_patch_torch_from_numpy')
dtype_names = ('float16','float32','float64','int8','int16','int32','int64','uint8','bool','complex64','complex128')
partial = SimpleNamespace(from_numpy=lambda arr: arr,
                          **{n:getattr(torch,n) for n in dtype_names})
ticks = []
def advance(_):
    assert not getattr(partial, '_vb_from_numpy_patched', False)
    ticks.append(1)
    if len(ticks)==3:
        partial.compile=lambda: None
gate = FunctionType(function_code, {'sys': SimpleNamespace(modules={'torch':partial}),
                                    '__builtins__':builtins.__dict__})
with patch('time.sleep', advance):
    gate()
assert len(ticks)==3 and partial._vb_from_numpy_patched
original = torch.from_numpy
def mismatch(_):
    raise RuntimeError('Numpy is not available')
torch.from_numpy = mismatch
torch._vb_from_numpy_patched = False
fallback = FunctionType(function_code, {'sys':sys, '__builtins__':builtins.__dict__})
try:
    fallback()
    assert torch._vb_from_numpy_patched
    for dtype in (np.float16,np.float32,np.int16,np.complex64):
        array = np.array([1,2,3],dtype=dtype)
        tensor = torch.from_numpy(array)
        np.testing.assert_array_equal(tensor.numpy(),array)
        assert tensor.dtype==getattr(torch,str(array.dtype))
    try:
        torch.from_numpy(np.array([1],dtype=np.uint64))
    except TypeError as error:
        assert 'unsupported numpy dtype' in str(error)
    else:
        raise AssertionError('Unsupported dtype silently accepted')
finally:
    torch.from_numpy = original
    torch._vb_from_numpy_patched = False
report={'status':'passed','cases':6,'partial_torch_import_defers_patch':True,
        'fallback_preserves_values_and_dtype':['float16','float32','int16','complex64'],
        'unsupported_dtype_rejected':True}
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
