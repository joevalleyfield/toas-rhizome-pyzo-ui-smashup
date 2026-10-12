"""Reviewable AST inventory of contextual Pyzo application entry points.

This checks syntactic references, including literal/dynamic getattr and imports;
owner/provenance correctness is established by the linked effects tests. It is
not a sandbox or a whole-program alias/dataflow proof.
"""

from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import tokenize

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "spikes/peer_frames/workspace_context_review.json"
ATTRIBUTES = frozenset(
    {
        "config",
        "editors",
        "shells",
        "toolManager",
        "commandHistory",
        "command_history",
        "main",
        "status",
        "runCommands",
        "shellCommands",
        "workspaceSession",
        "workspaceContext",
        "application",
        "metadata",
    }
)


def source_paths(root=ROOT):
    yield from sorted(
        (root / "deps/pyzo/pyzo").rglob("*.py"),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    # Product adapters/models live here too. Test-owned entry points are excluded.
    yield from sorted(
        (
            p
            for p in (root / "spikes/peer_frames").glob("*.py")
            if not p.name.startswith(("test_", "qt_", "workspace_context_audit"))
        ),
        key=lambda p: p.relative_to(root).as_posix(),
    )


def references(path, root=ROOT):
    # Python source encoding is independent of the Windows locale. Respect
    # coding cookies as well as the default UTF-8 source encoding.
    with tokenize.open(path) as source:
        tree = ast.parse(source.read())
    parents = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }
    aliases = {"pyzo"} | {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "pyzo"
    }
    imported = {
        alias.asname or alias.name: alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "pyzo"
        for alias in node.names
        if alias.name in ATTRIBUTES or alias.name == "*"
    }
    found = []
    for node in ast.walk(tree):
        attr = kind = None
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in aliases
            and node.attr in ATTRIBUTES
        ):
            attr, kind = node.attr, "attribute"
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"getattr", "setattr", "hasattr", "delattr"}
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in aliases
        ):
            value = node.args[1]
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                if value.value in ATTRIBUTES:
                    attr = value.value
            else:
                attr = "<dynamic>"
            kind = node.func.id
        elif isinstance(node, ast.Name) and node.id in imported:
            attr, kind = imported[node.id], "imported-name"
        elif isinstance(node, ast.ImportFrom) and node.module == "pyzo":
            names = sorted(
                alias.name
                for alias in node.names
                if alias.name in ATTRIBUTES or alias.name == "*"
            )
            if names:
                attr, kind = ",".join(names), "import"
        if attr is None:
            continue
        lineage, scope = [], tree
        up = parents.get(node)
        while up is not None:
            if isinstance(up, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                lineage.insert(0, up.name)
                if scope is tree:
                    scope = up
            up = parents.get(up)
        found.append(
            dict(
                file=path.relative_to(root).as_posix(),
                line=node.lineno,
                function=".".join(lineage) or "<module>",
                attribute=attr,
                kind=kind,
                expression=ast.unparse(node),
                scope_sha256=hashlib.sha256(
                    ast.dump(scope, include_attributes=False).encode()
                ).hexdigest(),
            )
        )
    return sorted(found, key=lambda row: (row["line"], row["kind"], row["expression"]))


def inventory(root=ROOT):
    return [row for path in source_paths(root) for row in references(path, root)]


def verify_review(root=ROOT):
    review = json.loads((root / REVIEW.relative_to(ROOT)).read_text())
    current = inventory(root)
    accepted = review["references"]
    assert current == [
        {
            key: value
            for key, value in row.items()
            if key not in {"classification", "proof"}
        }
        for row in accepted
    ], (
        "Global context consumers changed: review owner effects and update the inventory."
    )
    for row in accepted:
        assert row["classification"] in review["classifications"], row
        assert row["proof"] in review["proofs"], row
    return Counter(row["classification"] for row in accepted)


if __name__ == "__main__":
    print(
        json.dumps(
            dict(references=len(inventory()), classifications=verify_review()), indent=2
        )
    )
