"""Durable owner/source identity, availability and transactional overlay policy."""

from copy import deepcopy
import unittest

from spikes.peer_frames.breakpoint_overlays import BreakpointOverlays
from spikes.peer_frames.document_resources import DocumentResourceRegistry
from spikes.peer_frames.identity import IdentityKind, new_identity


class BreakpointOverlayTests(unittest.TestCase):
    def setUp(self):
        self.docs = DocumentResourceRegistry()
        self.a, self.b = [new_identity(IdentityKind.WORKSPACE) for _ in range(2)]
        self.doc = self.docs.create_document(
            "one\ntwo\nthree\n", path="/owned/source.py"
        )
        self.overlays = BreakpointOverlays(self.docs)
        self.overlays.replace(self.a, self.doc, [(2, True), (3, False)])
        self.overlays.replace(self.b, self.doc, [(1, True)])

    def test_independent_projection_and_persistence_without_open_views(self):
        self.assertEqual(self.overlays.project(self.a), {"/owned/source.py": [2]})
        self.assertEqual(self.overlays.project(self.b), {"/owned/source.py": [1]})
        restored = DocumentResourceRegistry()
        restored.restore_persistence_snapshot(self.docs.persistence_snapshot())
        overlays = BreakpointOverlays(restored)
        self.assertEqual(overlays.entries(self.a, self.doc), ((2, True), (3, False)))
        overlays.clear(self.a)
        self.assertEqual(overlays.project(self.b), {"/owned/source.py": [1]})
        self.assertEqual(overlays.project(self.a), {})

    def test_rename_same_identity_and_fork_copy_only_branching_owner(self):
        view = self.docs.open_view(self.doc, self.a)
        self.assertTrue(self.docs.rename_document(self.doc, "/owned/moved.py").applied)
        self.assertEqual(self.overlays.project(self.a), {"/owned/moved.py": [2]})
        branch = self.docs.branch_view(view)
        self.assertTrue(branch.applied)
        branch_id = self.docs.view(branch.view_id).document_id
        self.assertEqual(
            self.overlays.entries(self.a, branch_id), ((2, True), (3, False))
        )
        self.assertEqual(self.overlays.entries(self.b, branch_id), ())
        self.overlays.replace(self.a, branch_id, [(1, True)])
        self.assertEqual(
            self.overlays.entries(self.a, self.doc), ((2, True), (3, False))
        )
        self.assertEqual(
            self.overlays.project(self.a, {branch_id: "<branch>"}),
            {"/owned/moved.py": [2], "<branch>": [1]},
        )

    def test_unavailable_reactivation_and_path_reuse_cannot_inherit_identity(self):
        self.docs.mark_unavailable(self.doc)
        self.assertEqual(self.overlays.project(self.a), {})
        self.assertFalse(self.overlays.sources(self.a)[0].active)
        self.assertTrue(
            self.docs.rename_document(self.doc, "/owned/reactivated.py").applied
        )
        self.assertEqual(self.overlays.project(self.a), {"/owned/reactivated.py": [2]})
        self.assertTrue(self.docs.forget_document(self.doc))
        replacement = self.docs.create_document("replacement", path="/owned/source.py")
        self.assertEqual(self.overlays.entries(self.a, replacement), ())
        self.assertEqual(self.overlays.project(self.a), {})
        self.assertTrue(self.overlays.discard_broken(self.a, self.doc))
        self.assertEqual(self.overlays.entries(self.b, self.doc), ((1, True),))

    def test_invalid_edits_and_active_discard_leave_state_unchanged(self):
        before = deepcopy(self.docs.persistence_snapshot())
        for entries in ([(0, True)], [(1, 1)], [(True, True)], [(2, True), (2, False)]):
            with self.assertRaises(ValueError):
                self.overlays.replace(self.a, self.doc, entries)
            self.assertEqual(self.docs.persistence_snapshot(), before)
        self.assertFalse(self.overlays.discard_broken(self.a, self.doc))
        self.assertEqual(self.docs.persistence_snapshot(), before)

    def test_shared_edits_rebase_closed_owner_and_undo_without_changing_ownership(self):
        view = self.docs.open_view(self.doc, self.a)
        self.docs.replace_text(view, "inserted\none\ntwo\nthree\n")
        self.assertEqual(
            self.overlays.entries(self.a, self.doc), ((3, True), (4, False))
        )
        self.assertEqual(self.overlays.entries(self.b, self.doc), ((2, True),))
        self.assertTrue(self.docs.undo(view))
        self.assertEqual(
            self.overlays.entries(self.a, self.doc), ((2, True), (3, False))
        )
        self.assertEqual(self.overlays.entries(self.b, self.doc), ((1, True),))
        self.assertTrue(self.docs.redo(view))
        self.assertEqual(self.overlays.entries(self.b, self.doc), ((2, True),))


if __name__ == "__main__":
    unittest.main()
