"""Durable workspace/document overlays, independent of native text blocks."""

from dataclasses import dataclass
from copy import deepcopy
from difflib import SequenceMatcher

from .identity import ApplicationIdentity, IdentityKind


@dataclass(frozen=True)
class BreakpointSource:
    document_id: ApplicationIdentity
    path: str | None
    entries: tuple[tuple[int, bool], ...]
    active: bool


class BreakpointOverlays:
    extension = "workspace_breakpoints"

    def __init__(self, documents):
        self.documents = documents
        self._validate(self._state())

    def _state(self):
        return self.documents._persistence_extensions.get(
            self.extension, {"schema": 1, "owners": {}}
        )

    @staticmethod
    def _entries(entries):
        values = tuple(entries)
        if any(
            not isinstance(item, (list, tuple))
            or len(item) != 2
            or type(item[0]) is not int
            or item[0] < 1
            or type(item[1]) is not bool
            for item in values
        ):
            raise ValueError("breakpoints require positive lines and boolean state")
        if len({item[0] for item in values}) != len(values):
            raise ValueError("duplicate breakpoint line")
        return tuple(sorted((line, enabled) for line, enabled in values))

    def _validate(self, state):
        if (
            not isinstance(state, dict)
            or state.get("schema") != 1
            or not isinstance(state.get("owners"), dict)
        ):
            raise ValueError("invalid workspace breakpoint overlay")
        for owner, sources in state["owners"].items():
            ApplicationIdentity(IdentityKind.WORKSPACE, owner)
            if not isinstance(sources, dict):
                raise ValueError("invalid breakpoint sources")
            for identity, source in sources.items():
                ApplicationIdentity(IdentityKind.DOCUMENT, identity)
                if not isinstance(source, dict) or not isinstance(
                    source.get("path"), (str, type(None))
                ):
                    raise ValueError("invalid breakpoint source")
                self._entries(source["entries"])

    def entries(self, workspace_id, document_id):
        source = (
            self._state()["owners"].get(str(workspace_id), {}).get(str(document_id))
        )
        return self._entries(source["entries"]) if source else ()

    def replace(self, workspace_id, document_id, entries):
        if (
            workspace_id.kind is not IdentityKind.WORKSPACE
            or document_id.kind is not IdentityKind.DOCUMENT
        ):
            raise ValueError("breakpoint owner/source identity kinds are invalid")
        values = self._entries(entries)
        resource = self.documents.resource(document_id)
        state = deepcopy(self._state())
        sources = state["owners"].setdefault(str(workspace_id), {})
        if values:
            sources[str(document_id)] = {
                "path": resource.path,
                "entries": [list(item) for item in values],
            }
        else:
            sources.pop(str(document_id), None)
        self.documents._persistence_extensions[self.extension] = state

    def sources(self, workspace_id):
        result = []
        for identity, source in (
            self._state()["owners"].get(str(workspace_id), {}).items()
        ):
            document_id = ApplicationIdentity(IdentityKind.DOCUMENT, identity)
            try:
                resource = self.documents.resource(document_id)
            except KeyError:
                path, active = source["path"], False
            else:
                path = resource.path or source["path"]
                active = resource.available and (
                    resource.path is None
                    or self.documents._paths.get(resource.path) == document_id
                )
            result.append(
                BreakpointSource(
                    document_id, path, self.entries(workspace_id, document_id), active
                )
            )
        return tuple(result)

    def project(self, workspace_id, names=None):
        result = {}
        for source in self.sources(workspace_id):
            path = source.path or (names or {}).get(source.document_id)
            lines = [line for line, enabled in source.entries if enabled]
            if source.active and path and lines:
                result[path] = lines
        return result

    def copy_branch(self, workspace_id, source_id, target_id):
        self.replace(workspace_id, target_id, self.entries(workspace_id, source_id))

    def rebase(self, document_id, previous_text, text):
        """Track unchanged lines through shared edits, including closed owners."""
        if (
            previous_text == text
            or self.extension not in self.documents._persistence_extensions
        ):
            return
        old, new = previous_text.split("\n"), text.split("\n")
        mapping = {}
        for tag, a, b, c, d in SequenceMatcher(
            None, old, new, autojunk=False
        ).get_opcodes():
            if tag == "equal":
                mapping.update((line + 1, c + line - a + 1) for line in range(a, b))
            elif tag == "replace":
                mapping.update(
                    (a + offset + 1, c + offset + 1)
                    for offset in range(min(b - a, d - c))
                )
        state = deepcopy(self._state())
        for sources in state["owners"].values():
            source = sources.get(str(document_id))
            if source is not None:
                source["entries"] = [
                    [mapping[line], enabled]
                    for line, enabled in source["entries"]
                    if line in mapping
                ]
        self.documents._persistence_extensions[self.extension] = state

    def discard_broken(self, workspace_id, document_id):
        source = next(
            (
                source
                for source in self.sources(workspace_id)
                if source.document_id == document_id
            ),
            None,
        )
        if source is None or source.active:
            return False
        state = deepcopy(self._state())
        del state["owners"][str(workspace_id)][str(document_id)]
        self.documents._persistence_extensions[self.extension] = state
        return True

    def clear(self, workspace_id):
        state = deepcopy(self._state())
        state["owners"].pop(str(workspace_id), None)
        self.documents._persistence_extensions[self.extension] = state
