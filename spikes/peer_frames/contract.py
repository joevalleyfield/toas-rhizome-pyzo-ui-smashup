"""Application-owned workspace topology and backend contract.

The model deliberately contains no GUI toolkit types.  Pane state belongs to
the application; the backend receives complete layout snapshots and reports
user gestures as application-level events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, Mapping, Protocol


class PaneKind(str, Enum):
    EDITOR = "editor"
    SHELL = "shell"
    TOOL = "tool"
    RUN_DEBUG = "run-debug"
    CUSTOM = "custom"


class TabSide(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class Orientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Direction(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    ABOVE = "above"
    BELOW = "below"

    @property
    def orientation(self) -> Orientation:
        if self in (Direction.LEFT, Direction.RIGHT):
            return Orientation.HORIZONTAL
        return Orientation.VERTICAL

    @property
    def before(self) -> bool:
        return self in (Direction.LEFT, Direction.ABOVE)


class Capability(str, Enum):
    CREATE_FRAME = "create-frame"
    TAB = "tab"
    SPLIT = "split"
    OUTER_SPLIT = "outer-split"
    FLOAT = "float"
    MOVE_BETWEEN_FRAMES = "move-between-frames"
    CLOSE = "close"
    SAVE_RESTORE = "save-restore"
    TAB_SIDE = "tab-side"


class OperationStatus(str, Enum):
    APPLIED = "applied"
    UNSUPPORTED = "unsupported"
    REFUSED = "refused"
    CONFIRMATION_REQUIRED = "confirmation-required"
    CANCELLED = "cancelled"
    INVALID = "invalid"


@dataclass(frozen=True)
class OperationResult:
    status: OperationStatus
    detail: str = ""
    confirmations: tuple["CloseVote", ...] = ()

    @property
    def applied(self) -> bool:
        return self.status is OperationStatus.APPLIED


class CloseDecision(str, Enum):
    ALLOW = "allow"
    REFUSE = "refuse"
    CONFIRM = "confirm"


class CloseReason(str, Enum):
    PANE = "pane"
    GROUP = "group"
    FRAME = "frame"
    APPLICATION = "application"


@dataclass(frozen=True)
class CloseRequest:
    """Complete application transaction presented to every pane policy."""

    pane_ids: tuple[str, ...]
    reason: CloseReason


@dataclass(frozen=True)
class CloseVote:
    pane_id: str
    decision: CloseDecision
    detail: str = ""


class PaneClosePolicy(Protocol):
    def prepare_close(self, pane: "PaneDescriptor", request: CloseRequest) -> CloseVote:
        """Return a side-effect-free vote for a proposed close transaction."""

    def validate_close(self, pane: "PaneDescriptor", request: CloseRequest) -> CloseVote:
        """Revalidate after confirmation side effects and before topology commit."""

    def did_close(self, pane: "PaneDescriptor", request: CloseRequest) -> None:
        """Observe a close only after the whole transaction has committed."""


class _AllowClose:
    def prepare_close(self, pane: "PaneDescriptor", request: CloseRequest) -> CloseVote:
        return CloseVote(pane.id, CloseDecision.ALLOW)

    def validate_close(self, pane: "PaneDescriptor", request: CloseRequest) -> CloseVote:
        return CloseVote(pane.id, CloseDecision.ALLOW)

    def did_close(self, pane: "PaneDescriptor", request: CloseRequest) -> None:
        pass


@dataclass(frozen=True)
class PaneDescriptor:
    id: str
    kind: PaneKind
    title: str


@dataclass(frozen=True)
class ActiveContext:
    """Application identity currently targeted by commands and status."""

    pane: PaneDescriptor | None = None
    frame_id: str | None = None
    group_id: str | None = None


@dataclass
class _Group:
    id: str
    panes: list[str]
    active_pane_id: str
    tab_side: TabSide


@dataclass(frozen=True)
class _GroupNode:
    group_id: str


@dataclass(frozen=True)
class _SplitNode:
    orientation: Orientation
    children: tuple["_LayoutNode", ...]


_LayoutNode = _GroupNode | _SplitNode


@dataclass
class _Frame:
    id: str
    root: _LayoutNode
    groups: dict[str, _Group] = field(default_factory=dict)


class WorkspaceBackend(Protocol):
    capabilities: frozenset[Capability]

    def render(self, snapshot: Mapping[str, object]) -> None:
        """Make the backend reflect an application-owned layout snapshot."""


class BackendEventKind(str, Enum):
    ACTIVATE = "activate"
    TAB = "tab"
    SPLIT = "split"
    FLOAT = "float"
    REQUEST_CLOSE_PANE = "request-close-pane"
    REQUEST_CLOSE_GROUP = "request-close-group"
    REQUEST_CLOSE_FRAME = "request-close-frame"
    DESTROYED = "destroyed"


@dataclass(frozen=True)
class BackendEvent:
    kind: BackendEventKind
    pane_id: str | None = None
    group_id: str | None = None
    frame_id: str | None = None
    target_pane_id: str | None = None
    direction: Direction | None = None
    outer: bool = False


ConfirmClose = Callable[[tuple[CloseVote, ...]], bool]


class WorkspaceModel:
    """Authoritative peer-frame topology projected into a replaceable backend."""

    SCHEMA_VERSION = 2

    def __init__(self, backend: WorkspaceBackend):
        self.backend = backend
        self.panes: dict[str, PaneDescriptor] = {}
        self.frames: dict[str, _Frame] = {}
        self.active_pane_id: str | None = None
        self.shutdown_requested = False
        self._policies: dict[str, PaneClosePolicy] = {}
        self._next_frame = 1
        self._next_group = 1

    def register_pane(
        self,
        pane: PaneDescriptor,
        close_policy: PaneClosePolicy | None = None,
    ) -> OperationResult:
        if pane.id in self.panes:
            return self._invalid(f"pane already registered: {pane.id}")
        self.panes[pane.id] = pane
        self._policies[pane.id] = close_policy or _AllowClose()
        return self._applied()

    def set_close_policy(
        self, pane_id: str, close_policy: PaneClosePolicy
    ) -> OperationResult:
        if pane_id not in self.panes:
            return self._invalid(f"pane is not registered: {pane_id}")
        self._policies[pane_id] = close_policy
        return self._applied()

    def create_frame(self, pane_id: str, frame_id: str | None = None) -> OperationResult:
        unsupported = self._require(Capability.CREATE_FRAME)
        if unsupported:
            return unsupported
        invalid = self._require_unplaced_pane(pane_id)
        if invalid:
            return invalid
        frame_id = frame_id or self._new_frame_id()
        if frame_id in self.frames:
            return self._invalid(f"frame already exists: {frame_id}")
        group_id = self._new_group_id()
        group = _Group(
            group_id,
            [pane_id],
            pane_id,
            self._default_tab_side(self.panes[pane_id].kind),
        )
        self.frames[frame_id] = _Frame(frame_id, _GroupNode(group_id), {group_id: group})
        self.active_pane_id = pane_id
        self._publish()
        return self._applied()

    def tab(self, pane_id: str, target_pane_id: str) -> OperationResult:
        unsupported = self._require(Capability.TAB)
        if unsupported:
            return unsupported
        source = self._locate(pane_id)
        target = self._locate(target_pane_id)
        if source is None or target is None:
            return self._invalid("source and target panes must be placed")
        if pane_id == target_pane_id:
            return self._invalid("a pane cannot target itself")
        if source[0].id != target[0].id:
            unsupported = self._require(Capability.MOVE_BETWEEN_FRAMES)
            if unsupported:
                return unsupported
        if source[1].id == target[1].id:
            source[1].active_pane_id = pane_id
            self.active_pane_id = pane_id
            self._publish()
            return self._applied()
        self._detach(pane_id)
        target = self._locate(target_pane_id)
        assert target is not None
        target[1].panes.append(pane_id)
        target[1].active_pane_id = pane_id
        self.active_pane_id = pane_id
        self._publish()
        return self._applied()

    def split(
        self,
        pane_id: str,
        target_pane_id: str,
        direction: Direction,
        *,
        outer: bool = False,
    ) -> OperationResult:
        unsupported = self._require(Capability.OUTER_SPLIT if outer else Capability.SPLIT)
        if unsupported:
            return unsupported
        source = self._locate(pane_id)
        target = self._locate(target_pane_id)
        if source is None or target is None:
            return self._invalid("source and target panes must be placed")
        if pane_id == target_pane_id:
            return self._invalid("a pane cannot target itself")
        if source[0].id != target[0].id:
            unsupported = self._require(Capability.MOVE_BETWEEN_FRAMES)
            if unsupported:
                return unsupported

        target_frame_id = target[0].id
        target_group_id = target[1].id
        source_tab_side = source[1].tab_side
        self._detach(pane_id)
        frame = self.frames[target_frame_id]
        group_id = self._new_group_id()
        frame.groups[group_id] = _Group(
            group_id, [pane_id], pane_id, source_tab_side
        )
        new_node = _GroupNode(group_id)
        if outer:
            children = (new_node, frame.root) if direction.before else (frame.root, new_node)
            frame.root = _SplitNode(direction.orientation, children)
        else:
            frame.root = self._insert_local_split(
                frame.root, target_group_id, new_node, direction
            )
        self.active_pane_id = pane_id
        self._publish()
        return self._applied()

    def float(self, pane_id: str, frame_id: str | None = None) -> OperationResult:
        unsupported = self._require(Capability.FLOAT)
        if unsupported:
            return unsupported
        located = self._locate(pane_id)
        if located is None:
            return self._invalid(f"pane is not placed: {pane_id}")
        frame_id = frame_id or self._new_frame_id()
        if frame_id in self.frames:
            return self._invalid(f"frame already exists: {frame_id}")
        source_tab_side = located[1].tab_side
        self._detach(pane_id)
        group_id = self._new_group_id()
        group = _Group(group_id, [pane_id], pane_id, source_tab_side)
        self.frames[frame_id] = _Frame(frame_id, _GroupNode(group_id), {group_id: group})
        self.active_pane_id = pane_id
        self._publish()
        return self._applied()

    def activate(self, pane_id: str) -> OperationResult:
        located = self._locate(pane_id)
        if located is None:
            return self._invalid(f"pane is not placed: {pane_id}")
        located[1].active_pane_id = pane_id
        self.active_pane_id = pane_id
        self._publish()
        return self._applied()

    def adopt_backend_activation(self, pane_id: str) -> OperationResult:
        """Adopt settled UI focus without rendering topology back to the UI.

        This changes command context only.  It cannot establish an execution
        target or any other resource affinity.
        """

        located = self._locate(pane_id)
        if located is None:
            return self._invalid(f"pane is not placed: {pane_id}")
        located[1].active_pane_id = pane_id
        self.active_pane_id = pane_id
        return self._applied()

    def resolve_active_context(self) -> ActiveContext:
        """Resolve active application identity without exposing backend objects."""

        if self.active_pane_id is None:
            return ActiveContext()
        located = self._locate(self.active_pane_id)
        if located is None:
            return ActiveContext()
        frame, group = located
        return ActiveContext(
            pane=self.panes[self.active_pane_id],
            frame_id=frame.id,
            group_id=group.id,
        )

    def set_group_tab_side(
        self, group_id: str, tab_side: TabSide | str
    ) -> OperationResult:
        unsupported = self._require(Capability.TAB_SIDE)
        if unsupported:
            return unsupported
        try:
            tab_side = TabSide(tab_side)
        except ValueError:
            return self._invalid(f"unknown tab side: {tab_side}")
        group = next(
            (
                frame.groups[group_id]
                for frame in self.frames.values()
                if group_id in frame.groups
            ),
            None,
        )
        if group is None:
            return self._invalid(f"unknown group: {group_id}")
        group.tab_side = tab_side
        self._publish()
        return self._applied()

    def request_close_pane(
        self,
        pane_id: str,
        confirm: ConfirmClose | None = None,
    ) -> OperationResult:
        if self._locate(pane_id) is None:
            return self._invalid(f"pane is not placed: {pane_id}")
        return self._request_close((pane_id,), CloseReason.PANE, confirm)

    def request_close_frame(
        self,
        frame_id: str,
        confirm: ConfirmClose | None = None,
    ) -> OperationResult:
        unsupported = self._require(Capability.CLOSE)
        if unsupported:
            return unsupported
        frame = self.frames.get(frame_id)
        if frame is None:
            return self._invalid(f"unknown frame: {frame_id}")
        return self._request_close(tuple(self._frame_panes(frame)), CloseReason.FRAME, confirm)

    def request_close_group(
        self,
        group_id: str,
        confirm: ConfirmClose | None = None,
    ) -> OperationResult:
        unsupported = self._require(Capability.CLOSE)
        if unsupported:
            return unsupported
        group = next(
            (
                frame.groups[group_id]
                for frame in self.frames.values()
                if group_id in frame.groups
            ),
            None,
        )
        if group is None:
            return self._invalid(f"unknown group: {group_id}")
        return self._request_close(tuple(group.panes), CloseReason.GROUP, confirm)

    def request_shutdown(self, confirm: ConfirmClose | None = None) -> OperationResult:
        pane_ids = tuple(
            pane_id
            for frame in self.frames.values()
            for pane_id in self._frame_panes(frame)
        )
        result = self._request_close(pane_ids, CloseReason.APPLICATION, confirm)
        if result.applied:
            self.shutdown_requested = True
        return result

    def handle_backend_event(
        self,
        event: BackendEvent,
        confirm: ConfirmClose | None = None,
    ) -> OperationResult:
        if event.kind is BackendEventKind.ACTIVATE and event.pane_id:
            return self.activate(event.pane_id)
        if event.kind is BackendEventKind.TAB and event.pane_id and event.target_pane_id:
            return self.tab(event.pane_id, event.target_pane_id)
        if (
            event.kind is BackendEventKind.SPLIT
            and event.pane_id
            and event.target_pane_id
            and event.direction
        ):
            return self.split(
                event.pane_id,
                event.target_pane_id,
                event.direction,
                outer=event.outer,
            )
        if event.kind is BackendEventKind.FLOAT and event.pane_id:
            return self.float(event.pane_id, event.frame_id)
        if event.kind is BackendEventKind.REQUEST_CLOSE_PANE and event.pane_id:
            return self.request_close_pane(event.pane_id, confirm)
        if event.kind is BackendEventKind.REQUEST_CLOSE_GROUP and event.group_id:
            return self.request_close_group(event.group_id, confirm)
        if event.kind is BackendEventKind.REQUEST_CLOSE_FRAME and event.frame_id:
            return self.request_close_frame(event.frame_id, confirm)
        if event.kind is BackendEventKind.DESTROYED:
            self._publish()
            return self._invalid(
                "backend destruction cannot bypass application close negotiation"
            )
        return self._invalid("incomplete or unknown backend event")

    def serialize_layout(self) -> dict[str, object]:
        return {
            "schema": self.SCHEMA_VERSION,
            "active_pane_id": self.active_pane_id,
            "frames": [self._serialize_frame(frame) for frame in self.frames.values()],
        }

    def restore_layout(self, layout: Mapping[str, object]) -> OperationResult:
        unsupported = self._require(Capability.SAVE_RESTORE)
        if unsupported:
            return unsupported
        try:
            frames, active = self._parse_layout(layout)
        except (KeyError, TypeError, ValueError) as error:
            return self._invalid(f"invalid layout: {error}")

        self.frames = {frame.id: frame for frame in frames}
        self.active_pane_id = active
        self._publish()
        return self._applied()

    def adopt_backend_layout(self, layout: Mapping[str, object]) -> OperationResult:
        """Atomically adopt a settled placement-only layout from a backend.

        A backend gesture may rearrange existing panes, but it cannot create or
        close application panes. Invalid foreign state is rejected without a
        partial model mutation and without rendering back into the backend.
        """

        before = {
            pane_id
            for frame in self.frames.values()
            for pane_id in self._frame_panes(frame)
        }
        try:
            frames, active = self._parse_layout(layout)
            after = {
                pane_id for frame in frames for pane_id in self._frame_panes(frame)
            }
            if after != before:
                missing = sorted(before.difference(after))
                added = sorted(after.difference(before))
                raise ValueError(
                    f"backend changed pane membership; missing={missing}, added={added}"
                )
        except (KeyError, TypeError, ValueError) as error:
            return self._invalid(f"invalid backend layout: {error}")

        self.frames = {frame.id: frame for frame in frames}
        self.active_pane_id = active
        return self._applied()

    def _request_close(
        self,
        pane_ids: tuple[str, ...],
        reason: CloseReason,
        confirm: ConfirmClose | None,
    ) -> OperationResult:
        unsupported = self._require(Capability.CLOSE)
        if unsupported:
            return unsupported
        request = CloseRequest(pane_ids, reason)
        votes = tuple(
            self._policies[pane_id].prepare_close(self.panes[pane_id], request)
            for pane_id in pane_ids
        )
        refusals = tuple(vote for vote in votes if vote.decision is CloseDecision.REFUSE)
        if refusals:
            return OperationResult(OperationStatus.REFUSED, refusals[0].detail, refusals)
        confirmations = tuple(
            vote for vote in votes if vote.decision is CloseDecision.CONFIRM
        )
        if confirmations and confirm is None:
            return OperationResult(
                OperationStatus.CONFIRMATION_REQUIRED,
                "close requires confirmation",
                confirmations,
            )
        if confirmations and confirm is not None and not confirm(confirmations):
            return OperationResult(
                OperationStatus.CANCELLED,
                "close confirmation was cancelled",
                confirmations,
            )

        validations = tuple(
            self._policies[pane_id].validate_close(self.panes[pane_id], request)
            for pane_id in pane_ids
        )
        validation_failures = tuple(
            vote for vote in validations if vote.decision is not CloseDecision.ALLOW
        )
        if validation_failures:
            return OperationResult(
                OperationStatus.REFUSED,
                validation_failures[0].detail,
                validation_failures,
            )

        descriptors = [self.panes[pane_id] for pane_id in pane_ids]
        policies = [self._policies[pane_id] for pane_id in pane_ids]
        for pane_id in pane_ids:
            if self._locate(pane_id):
                self._detach(pane_id)
            self.panes.pop(pane_id, None)
            self._policies.pop(pane_id, None)
        self._choose_active_pane()
        self._publish()
        for policy, pane in zip(policies, descriptors):
            policy.did_close(pane, request)
        return self._applied()

    def _detach(self, pane_id: str) -> None:
        located = self._locate(pane_id)
        if located is None:
            raise ValueError(f"pane is not placed: {pane_id}")
        frame, group = located
        group.panes.remove(pane_id)
        if group.panes:
            if group.active_pane_id == pane_id:
                group.active_pane_id = group.panes[-1]
            return
        del frame.groups[group.id]
        replacement = self._remove_group(frame.root, group.id)
        if replacement is None:
            del self.frames[frame.id]
        else:
            frame.root = replacement

    def _locate(self, pane_id: str) -> tuple[_Frame, _Group] | None:
        for frame in self.frames.values():
            for group in frame.groups.values():
                if pane_id in group.panes:
                    return frame, group
        return None

    def _require_unplaced_pane(self, pane_id: str) -> OperationResult | None:
        if pane_id not in self.panes:
            return self._invalid(f"pane is not registered: {pane_id}")
        if self._locate(pane_id):
            return self._invalid(f"pane is already placed: {pane_id}")
        return None

    def _require(self, capability: Capability) -> OperationResult | None:
        if capability not in self.backend.capabilities:
            return OperationResult(
                OperationStatus.UNSUPPORTED,
                f"backend does not provide {capability.value}",
            )
        return None

    def _insert_local_split(
        self,
        node: _LayoutNode,
        target_group_id: str,
        new_node: _GroupNode,
        direction: Direction,
    ) -> _LayoutNode:
        if isinstance(node, _GroupNode):
            if node.group_id != target_group_id:
                return node
            children = (new_node, node) if direction.before else (node, new_node)
            return _SplitNode(direction.orientation, children)
        children = list(node.children)
        for index, child in enumerate(children):
            replaced = self._insert_local_split(
                child, target_group_id, new_node, direction
            )
            if replaced is not child:
                if node.orientation is direction.orientation and isinstance(
                    replaced, _SplitNode
                ) and replaced.orientation is node.orientation:
                    children[index : index + 1] = list(replaced.children)
                else:
                    children[index] = replaced
                return _SplitNode(node.orientation, tuple(children))
        return node

    def _remove_group(self, node: _LayoutNode, group_id: str) -> _LayoutNode | None:
        if isinstance(node, _GroupNode):
            return None if node.group_id == group_id else node
        children: list[_LayoutNode] = []
        for child in node.children:
            remaining = self._remove_group(child, group_id)
            if remaining is not None:
                children.append(remaining)
        if not children:
            return None
        if len(children) == 1:
            return children[0]
        return _SplitNode(node.orientation, tuple(children))

    def _frame_panes(self, frame: _Frame) -> Iterable[str]:
        for group_id in self._group_ids(frame.root):
            yield from frame.groups[group_id].panes

    def _group_ids(self, node: _LayoutNode) -> Iterable[str]:
        if isinstance(node, _GroupNode):
            yield node.group_id
            return
        for child in node.children:
            yield from self._group_ids(child)

    def _choose_active_pane(self) -> None:
        if self.active_pane_id and self._locate(self.active_pane_id):
            return
        self.active_pane_id = next(
            (
                pane_id
                for frame in reversed(tuple(self.frames.values()))
                for pane_id in self._frame_panes(frame)
            ),
            None,
        )

    def _serialize_frame(self, frame: _Frame) -> dict[str, object]:
        return {
            "id": frame.id,
            "root": self._serialize_node(frame.root),
            "groups": [
                {
                    "id": group.id,
                    "panes": list(group.panes),
                    "active_pane_id": group.active_pane_id,
                    "tab_side": group.tab_side.value,
                }
                for group_id in self._group_ids(frame.root)
                for group in (frame.groups[group_id],)
            ],
        }

    def _parse_layout(
        self, layout: Mapping[str, object]
    ) -> tuple[list[_Frame], str | None]:
        if layout["schema"] != self.SCHEMA_VERSION:
            raise ValueError("unsupported schema")
        raw_frames = layout["frames"]
        if not isinstance(raw_frames, list):
            raise ValueError("frames must be a list")
        frames = [self._deserialize_frame(item) for item in raw_frames]
        frame_ids = [frame.id for frame in frames]
        if len(frame_ids) != len(set(frame_ids)):
            raise ValueError("duplicate frame identity")
        group_ids = [group_id for frame in frames for group_id in frame.groups]
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("duplicate group identity")
        placed = [pane for frame in frames for pane in self._frame_panes(frame)]
        if len(placed) != len(set(placed)):
            raise ValueError("a pane appears more than once")
        missing = set(placed).difference(self.panes)
        if missing:
            raise ValueError(f"unregistered panes: {sorted(missing)}")
        active = layout.get("active_pane_id")
        if active is not None and not isinstance(active, str):
            raise ValueError("active pane identity must be a string or null")
        if active is not None and active not in placed:
            raise ValueError("active pane is not placed")
        return frames, active

    def _serialize_node(self, node: _LayoutNode) -> dict[str, object]:
        if isinstance(node, _GroupNode):
            return {"type": "group", "group_id": node.group_id}
        return {
            "type": "split",
            "orientation": node.orientation.value,
            "children": [self._serialize_node(child) for child in node.children],
        }

    def _deserialize_frame(self, raw: object) -> _Frame:
        if not isinstance(raw, Mapping):
            raise ValueError("frame must be an object")
        frame_id = raw["id"]
        raw_groups = raw["groups"]
        if not isinstance(frame_id, str) or not isinstance(raw_groups, list):
            raise ValueError("invalid frame fields")
        groups: dict[str, _Group] = {}
        for item in raw_groups:
            if not isinstance(item, Mapping):
                raise ValueError("group must be an object")
            group_id = item["id"]
            panes = item["panes"]
            active = item["active_pane_id"]
            try:
                tab_side = TabSide(item["tab_side"])
            except ValueError as error:
                raise ValueError(f"invalid tab side: {item['tab_side']}") from error
            if (
                not isinstance(group_id, str)
                or not isinstance(panes, list)
                or not all(isinstance(pane, str) for pane in panes)
                or not isinstance(active, str)
                or active not in panes
            ):
                raise ValueError("invalid group fields")
            if group_id in groups:
                raise ValueError("duplicate group identity")
            groups[group_id] = _Group(group_id, list(panes), active, tab_side)
        root = self._deserialize_node(raw["root"])
        referenced = list(self._group_ids(root))
        if set(referenced) != set(groups) or len(referenced) != len(groups):
            raise ValueError("layout tree and groups disagree")
        return _Frame(frame_id, root, groups)

    def _deserialize_node(self, raw: object) -> _LayoutNode:
        if not isinstance(raw, Mapping):
            raise ValueError("layout node must be an object")
        if raw.get("type") == "group" and isinstance(raw.get("group_id"), str):
            return _GroupNode(raw["group_id"])
        if raw.get("type") == "split":
            children = raw.get("children")
            if not isinstance(children, list) or len(children) < 2:
                raise ValueError("a split needs at least two children")
            return _SplitNode(
                Orientation(raw["orientation"]),
                tuple(self._deserialize_node(child) for child in children),
            )
        raise ValueError("unknown layout node")

    def _publish(self) -> None:
        self.backend.render(self.serialize_layout())

    def _new_frame_id(self) -> str:
        while f"frame-{self._next_frame}" in self.frames:
            self._next_frame += 1
        value = f"frame-{self._next_frame}"
        self._next_frame += 1
        return value

    def _new_group_id(self) -> str:
        existing = {group_id for frame in self.frames.values() for group_id in frame.groups}
        while f"group-{self._next_group}" in existing:
            self._next_group += 1
        value = f"group-{self._next_group}"
        self._next_group += 1
        return value

    @staticmethod
    def _default_tab_side(pane_kind: PaneKind) -> TabSide:
        if pane_kind is PaneKind.EDITOR:
            return TabSide.TOP
        if pane_kind in (PaneKind.SHELL, PaneKind.TOOL, PaneKind.RUN_DEBUG):
            return TabSide.BOTTOM
        return TabSide.TOP

    @staticmethod
    def _applied() -> OperationResult:
        return OperationResult(OperationStatus.APPLIED)

    @staticmethod
    def _invalid(detail: str) -> OperationResult:
        return OperationResult(OperationStatus.INVALID, detail)
