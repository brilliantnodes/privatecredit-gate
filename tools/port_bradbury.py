"""Make the Bradbury Phase 2 (GenVM v0.6) build of a contract written for Studio (GenVM v0.2).

    python3 port.py <source.py> <out.py> [--pack]

Rewrites, in the direction of GenLayer Foundation's own Studio/Bradbury targets
(genlayer-foundation/uptime, contracts/targets.json):
  header      -> # { "Seq": [{"Depends": "py-genlayer:babwp9t3...0"}] }
  from genlayer import *  -> import genlayer as gl; storage and types imported explicitly
  gl.Contract             -> gl.contract.Contract
  gl.vm.run_nondet_unsafe -> gl.vm.run_nondet
  gl.message_raw[         -> gl.message.raw[
  gl.get_contract_at(     -> gl.contract.get_at(
Then docstrings and comments are stripped and indentation shrunk, so the deploy
fits under Bradbury's per-transaction gas cap. The script asserts that the
output's AST equals the source's AST after applying exactly these renames, and
that no Studio-only construct is left.

--pack (for contracts still above the limit after stripping, such as RigSettle):
the stripped code is zlib-compressed and base85-encoded inside a two-line stub
that decompresses and executes it in the module namespace at load time. The
script asserts the round trip is lossless; the unpacked code is the stripped
build, which is also written next to the output as <out>.unpacked.py.
"""
import ast
import base64
import re
import sys
import zlib

RUNNER = "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0"
HEADER = '# { "Seq": [{"Depends": "%s"}] }\n' % RUNNER
IMPORTS = "import genlayer as gl\nfrom genlayer.storage import DynArray, TreeMap, allow as allow_storage\nfrom genlayer.types import *\n"
RENAMES = [
    (r"\bgl\.Contract\b", "gl.contract.Contract"),
    (r"\bgl\.vm\.run_nondet_unsafe\(", "gl.vm.run_nondet("),
    (r"\bgl\.message_raw\[", "gl.message.raw["),
    (r"\bgl\.get_contract_at\(", "gl.contract.get_at("),
]
FORBID = ["from genlayer import *", "gl.Contract)", "run_nondet_unsafe", "message_raw", "get_contract_at", "py-genlayer:1jb45"]


def strip_docstrings(tree):
    for n in ast.walk(tree):
        body = getattr(n, "body", None)
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and body \
                and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            n.body = body[1:] or [ast.Pass()]
    return tree


def renamed(src: str) -> str:
    lines = src.split("\n")
    assert lines[0].startswith('# { "Depends"'), "line 1 must be the Studio Depends header"
    body = "\n".join(lines[1:])
    n = body.count("from genlayer import *\n")
    assert n == 1, f"expected one star import, found {n}"
    body = body.replace("from genlayer import *\n", IMPORTS)
    for pat, rep in RENAMES:
        body = re.sub(pat, rep, body)
    return body


def pack(code: str) -> str:
    """Two-line stub that rebuilds and runs the stripped code."""
    blob = base64.b85encode(zlib.compress(code.encode(), 9)).decode()
    assert zlib.decompress(base64.b85decode(blob)).decode() == code, "pack round trip failed"
    return "import base64, zlib\nexec(zlib.decompress(base64.b85decode(" + repr(blob) + ")).decode())\n"


def main(src_path, out_path, packed=False):
    src = open(src_path).read()
    body = renamed(src)
    small = ast.unparse(strip_docstrings(ast.parse(body)))
    small = "\n".join(re.sub(r"^((?:    )+)", lambda m: " " * (len(m.group(1)) // 4), line) for line in small.split("\n"))
    out = HEADER + small + "\n"
    assert ast.dump(ast.parse(out)) == ast.dump(strip_docstrings(ast.parse(body))), "AST changed beyond the renames"
    for bad in FORBID:
        assert bad not in out, f"Studio-only construct left: {bad}"
    if packed:
        open(out_path[:-3] + ".unpacked.py", "w").write(out)
        out = HEADER + pack(small + "\n")
    open(out_path, "w").write(out)
    print(f"{src_path.split('/')[-1]}: {len(src)} -> {len(out)} bytes" + (" (packed)" if packed else ""))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--pack" in sys.argv[3:])
