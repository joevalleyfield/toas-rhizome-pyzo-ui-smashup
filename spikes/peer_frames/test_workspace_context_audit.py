"""Any changed direct context consumer must carry a reviewed owner proof."""

import json
from spikes.peer_frames.workspace_context_audit import (
    ROOT,
    REVIEW,
    inventory,
    references,
    verify_review,
)


def test_current_context_inventory_has_no_unreviewed_consumers():
    counts = verify_review()
    assert sum(counts.values()) == len(inventory())
    review = json.loads(REVIEW.read_text())
    for proof in review["proofs"].values():
        assert proof["invariant"]
        assert all((ROOT / path).is_file() for path in proof["files"])


def test_alias_literal_dynamic_and_import_consumers_are_visible(tmp_path):
    source = tmp_path / "consumer.py"
    source.write_text(
        "import pyzo as other\nfrom pyzo import editors as local\n"
        'other.editors.loadFile("a")\ngetattr(other,"shells")\n'
        "getattr(other,key)\nlocal.newFile()\n"
    )
    found = references(source, tmp_path)
    assert {(row["kind"], row["attribute"]) for row in found} == {
        ("attribute", "editors"),
        ("getattr", "shells"),
        ("getattr", "<dynamic>"),
        ("import", "editors"),
        ("imported-name", "editors"),
    }
