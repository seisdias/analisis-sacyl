# tools/find_reachable.py
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENTRYPOINTS = [
    ROOT / "app" / "web_main.py",
    ROOT / "api" / "server.py",
]

# Solo analizamos imports internos (archivos .py del repo)
ALL_PY = {p.relative_to(ROOT): p for p in ROOT.rglob("*.py")}

def norm_mod(name: str) -> str:
    return name.strip().replace("-", "_")

def candidates_for_module(mod: str) -> list[Path]:
    # mod como "api.deps" o "db.db_manager"
    parts = mod.split(".")
    out = []
    # api/deps.py
    p1 = ROOT.joinpath(*parts).with_suffix(".py")
    if p1.exists():
        out.append(p1)
    # api/deps/__init__.py
    p2 = ROOT.joinpath(*parts) / "__init__.py"
    if p2.exists():
        out.append(p2)
    return out

def parse_imports(py_file: Path) -> set[str]:
    src = py_file.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(src, filename=str(py_file))
    mods = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(norm_mod(alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base = norm_mod(node.module)
                # from api import server  -> api.server (posible)
                if node.level == 0:
                    mods.add(base)
                    for alias in node.names:
                        mods.add(f"{base}.{norm_mod(alias.name)}")
                else:
                    # imports relativos: resolvemos “a ojo” con el path actual
                    # (suficiente para triage; lo importante es no borrar)
                    mods.add(base)
    return mods

reachable: set[Path] = set()
queue: list[Path] = [p for p in ENTRYPOINTS if p.exists()]

while queue:
    f = queue.pop()
    if f in reachable:
        continue
    reachable.add(f)

    for mod in parse_imports(f):
        for cand in candidates_for_module(mod):
            if cand.exists() and cand not in reachable:
                queue.append(cand)

# Report
rel_reachable = sorted(p.relative_to(ROOT) for p in reachable)
print("REACHABLE (.py):")
for p in rel_reachable:
    print("  ", p)

# Everything else
unreach = sorted(set(ALL_PY.keys()) - set(rel_reachable))
print("\nUNREACHABLE (.py) [candidatos legacy]:")
for p in unreach:
    print("  ", p)
