"""Pure incremental planning and immutable evidence handling for admission."""

from __future__ import annotations

import fcntl
import os
import stat
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator

from pydantic import ValidationError

from ..contracts.admission_keeper import (
    AdmissionEvidenceNode,
    AdmissionEvidenceNodeStatement,
    AdmissionKeeperRefreshPlan,
    AdmissionKeeperCycle,
    AdmissionKeeperSpec,
    AdmissionKeeperStageState,
    AdmissionKeeperState,
    KeeperCurrentness,
    KeeperRefreshAction,
    KeeperRefreshStep,
)
from ..contracts.control_plane import canonical_digest
from ..errors import AoASDKError
from .registry import canonical_json_bytes, reject_secret_material


class AdmissionKeeperError(AoASDKError, ValueError):
    """Keeper evidence or state is invalid, conflicting, stale, or unauthorized."""


def materialize_keeper_spec(spec: AdmissionKeeperSpec) -> AdmissionKeeperSpec:
    expected = canonical_digest(spec, exclude={"spec_id"})
    if spec.spec_id == "sha256:" + "0" * 64:
        return spec.model_copy(update={"spec_id": expected})
    if spec.spec_id != expected:
        raise AdmissionKeeperError("keeper spec digest mismatch")
    return spec


def materialize_evidence_node(
    statement: AdmissionEvidenceNodeStatement,
    spec: AdmissionKeeperSpec,
    existing_nodes: Iterable[AdmissionEvidenceNode] = (),
) -> AdmissionEvidenceNode:
    spec = materialize_keeper_spec(spec)
    _assert_node_statement(statement, spec, tuple(existing_nodes))
    placeholder = AdmissionEvidenceNode(
        **statement.model_dump(mode="python"),
        node_id="sha256:" + "0" * 64,
    )
    return placeholder.model_copy(
        update={"node_id": canonical_digest(placeholder, exclude={"node_id"})}
    )


def assert_evidence_node(
    node: AdmissionEvidenceNode,
    spec: AdmissionKeeperSpec,
    existing_nodes: Iterable[AdmissionEvidenceNode] = (),
) -> None:
    expected = canonical_digest(node, exclude={"node_id"})
    if node.node_id != expected:
        raise AdmissionKeeperError("keeper evidence node digest mismatch")
    statement = AdmissionEvidenceNodeStatement.model_validate(
        node.model_dump(mode="python", exclude={"node_id"})
    )
    _assert_node_statement(statement, materialize_keeper_spec(spec), tuple(existing_nodes))


def plan_keeper_refresh(
    spec: AdmissionKeeperSpec,
    *,
    nodes: Iterable[AdmissionEvidenceNode] = (),
    prior_state: AdmissionKeeperState | None = None,
    planned_at: datetime | None = None,
    renewal_margin_seconds: int = 60,
) -> AdmissionKeeperRefreshPlan:
    spec = materialize_keeper_spec(spec)
    now = _aware_utc(planned_at or datetime.now(timezone.utc))
    if renewal_margin_seconds < 0:
        raise AdmissionKeeperError("renewal margin cannot be negative")
    refresh_before = now + timedelta(seconds=renewal_margin_seconds)
    spec_expired = spec.expires_at <= now
    node_map = _latest_nodes(nodes)
    selected: dict[str, str] = {}
    actions: dict[str, str] = {}
    steps: list[KeeperRefreshStep] = []
    for stage_spec in spec.stages:
        stage = stage_spec.stage
        stage_digest = canonical_digest(stage_spec)
        prior = node_map.get(stage)
        reasons: list[str] = []
        if spec_expired:
            reasons.append("keeper_spec_expired")
        dependency_ids: list[str] = []
        dependency_refresh = False
        for dependency in stage_spec.dependency_stages:
            if actions.get(dependency) != "reuse":
                dependency_refresh = True
            node_id = selected.get(dependency)
            if node_id is not None:
                dependency_ids.append(node_id)
        if prior is None:
            reasons.append("evidence_absent")
        else:
            try:
                _assert_compatible_node(prior, spec, node_map.values())
            except AdmissionKeeperError:
                reasons.append("evidence_invalid")
            if prior.stage_spec_digest != stage_digest:
                reasons.append("stage_input_changed")
            if prior.subject_digest != stage_spec.subject_digest:
                reasons.append("subject_changed")
            if prior.expires_at <= refresh_before:
                reasons.append("evidence_expiring")
            if prior.outcome != "passed":
                reasons.append(f"evidence_{prior.outcome}")
            if tuple(dependency_ids) != prior.dependency_node_ids:
                reasons.append("dependency_identity_changed")
        if dependency_refresh:
            reasons.append("dependency_refresh_required")
        reasons = list(dict.fromkeys(reasons))
        action: KeeperRefreshAction
        if spec_expired:
            action = "blocked"
            cost = 0
        elif not reasons and prior is not None:
            action = "reuse"
            selected[stage] = prior.node_id
            cost = 0
        elif not stage_spec.automatic_execution_allowed:
            action = "blocked"
            cost = 0
            reasons.append("owner_issued_evidence_required")
        else:
            action = "refresh"
            cost = stage_spec.cost_weight
        actions[stage] = action
        steps.append(
            KeeperRefreshStep(
                stage=stage,
                action=action,
                owner=stage_spec.owner,
                prior_node_id=prior.node_id if prior is not None else None,
                dependency_node_ids=tuple(dependency_ids),
                reason_codes=tuple(dict.fromkeys(reasons)),
                cost_weight=cost,
            )
        )
    full_cost = sum(item.cost_weight for item in spec.stages)
    placeholder = AdmissionKeeperRefreshPlan(
        plan_id="sha256:" + "0" * 64,
        spec_id=spec.spec_id,
        prior_state_id=prior_state.state_id if prior_state is not None else None,
        organ_id=spec.organ_id,
        contour_id=spec.contour_id,
        planned_at=now,
        refresh_before=refresh_before,
        steps=tuple(steps),
        full_refresh_cost=full_cost,
        planned_refresh_cost=sum(item.cost_weight for item in steps),
        reused_stage_count=sum(item.action == "reuse" for item in steps),
        refreshed_stage_count=sum(item.action == "refresh" for item in steps),
        blocked_stage_count=sum(item.action == "blocked" for item in steps),
    )
    return placeholder.model_copy(
        update={"plan_id": canonical_digest(placeholder, exclude={"plan_id"})}
    )


def build_keeper_state(
    spec: AdmissionKeeperSpec,
    *,
    nodes: Iterable[AdmissionEvidenceNode],
    prior_state: AdmissionKeeperState | None = None,
    updated_at: datetime | None = None,
    last_good_state_ref: str | None = None,
    last_good_state_digest: str | None = None,
) -> AdmissionKeeperState:
    spec = materialize_keeper_spec(spec)
    now = _aware_utc(updated_at or datetime.now(timezone.utc))
    node_map = _latest_nodes(nodes)
    stage_states: list[AdmissionKeeperStageState] = []
    blockers: list[str] = []
    next_stage = None
    passed: set[str] = set()
    spec_expired = spec.expires_at <= now
    for stage_spec in spec.stages:
        node = node_map.get(stage_spec.stage)
        reasons: list[str] = []
        if spec_expired:
            reasons.append("keeper_spec_expired")
        current = False
        if node is None:
            reasons.append("evidence_absent")
        else:
            try:
                _assert_compatible_node(node, spec, node_map.values())
            except AdmissionKeeperError:
                reasons.append("evidence_invalid")
            if node.expires_at <= now:
                reasons.append("evidence_expired")
            if node.outcome != "passed":
                reasons.append(f"evidence_{node.outcome}")
            missing_dependencies = set(stage_spec.dependency_stages) - passed
            if missing_dependencies:
                reasons.append("dependency_not_current")
            current = not reasons
        if current:
            passed.add(stage_spec.stage)
        else:
            blockers.extend(reasons)
            if next_stage is None:
                next_stage = stage_spec.stage
        stage_states.append(
            AdmissionKeeperStageState(
                stage=stage_spec.stage,
                node_id=node.node_id if node is not None else None,
                outcome=node.outcome if node is not None else None,
                expires_at=node.expires_at if node is not None else None,
                current=current,
                reason_codes=tuple(dict.fromkeys(reasons)),
            )
        )
    currentness = _classify_currentness(passed, bool(blockers), last_good_state_ref)
    admitted = (
        "registry_admission" in passed
        and "consumer_observation" in passed
        and not blockers
        and spec.expires_at > now
    )
    if not admitted and "admitted" in currentness:
        currentness = tuple(item for item in currentness if item != "admitted")
    placeholder = AdmissionKeeperState(
        state_id="sha256:" + "0" * 64,
        revision=(prior_state.revision + 1 if prior_state is not None else 1),
        spec_id=spec.spec_id,
        organ_id=spec.organ_id,
        contour_id=spec.contour_id,
        transaction_ref=spec.transaction_ref,
        updated_at=now,
        stages=tuple(stage_states),
        currentness=currentness,
        admission_current=admitted,
        last_good_state_ref=last_good_state_ref,
        last_good_state_digest=last_good_state_digest,
        blocker_codes=tuple(dict.fromkeys(blockers)),
        next_safe_stage=next_stage,
    )
    return placeholder.model_copy(
        update={"state_id": canonical_digest(placeholder, exclude={"state_id"})}
    )


class KeeperEvidenceStore:
    """Immutable content-addressed node store with an explicit latest state."""

    def __init__(self, root: str | Path):
        # Do not resolve the final component: a caller-supplied symlink must be
        # rejected rather than silently converted into its target directory.
        self.root = Path(os.path.abspath(Path(root).expanduser()))
        self.nodes_root = self.root / "nodes"
        self.states_root = self.root / "states"
        self.plans_root = self.root / "plans"
        self.lock_path = self.root / ".keeper.lock"
        if self.root.is_symlink() or (
            self.root.exists() and not self.root.is_dir()
        ):
            raise AdmissionKeeperError("keeper root must be a non-symlink directory")
        self.nodes_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.states_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.plans_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for path, label in (
            (self.nodes_root, "nodes"),
            (self.states_root, "states"),
            (self.plans_root, "plans"),
        ):
            if path.is_symlink() or not path.is_dir():
                raise AdmissionKeeperError(
                    f"keeper {label} root must be a non-symlink directory"
                )
        os.chmod(self.root, 0o700)
        os.chmod(self.nodes_root, 0o700)
        os.chmod(self.states_root, 0o700)
        os.chmod(self.plans_root, 0o700)
        if self.lock_path.is_symlink():
            raise AdmissionKeeperError(
                "keeper lock must be a regular non-symlink file"
            )
        try:
            fd = os.open(
                self.lock_path,
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        except FileExistsError:
            pass
        else:
            os.close(fd)
        if self.lock_path.is_symlink() or not self.lock_path.is_file():
            raise AdmissionKeeperError(
                "keeper lock must be a regular non-symlink file"
            )
        os.chmod(self.lock_path, 0o600)

    @contextmanager
    def cycle_lock(self) -> Iterator[None]:
        """Serialize one complete import/plan/state CAS transaction."""

        try:
            fd = os.open(
                self.lock_path,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            )
        except OSError as exc:
            raise AdmissionKeeperError("keeper lock cannot be opened safely") from exc
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise AdmissionKeeperError("keeper lock must remain a regular file")
        with os.fdopen(fd, "rb") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def put_node(self, node: AdmissionEvidenceNode) -> Path:
        reject_secret_material(node.model_dump(mode="json"), context="keeper node")
        path = self.nodes_root / f"{node.node_id[7:]}.json"
        payload = canonical_json_bytes(node.model_dump(mode="json")) + b"\n"
        if path.exists():
            if path.is_symlink() or path.read_bytes() != payload:
                raise AdmissionKeeperError("keeper node content-address conflict")
            return path
        _atomic_write(path, payload, exclusive=True)
        return path

    def load_nodes(self) -> tuple[AdmissionEvidenceNode, ...]:
        nodes: list[AdmissionEvidenceNode] = []
        for path in sorted(self.nodes_root.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                raise AdmissionKeeperError("keeper node path is not a regular file")
            try:
                node = AdmissionEvidenceNode.model_validate_json(path.read_bytes())
            except ValidationError as exc:
                raise AdmissionKeeperError(f"invalid keeper node {path}") from exc
            if path.stem != node.node_id[7:]:
                raise AdmissionKeeperError("keeper node filename digest mismatch")
            nodes.append(node)
        return tuple(nodes)

    def publish_state(
        self,
        state: AdmissionKeeperState,
        *,
        expected_prior_state_id: str | None,
    ) -> Path:
        latest = self.root / "latest.json"
        prior = None
        if latest.exists():
            if latest.is_symlink() or not latest.is_file():
                raise AdmissionKeeperError("keeper latest state must be a regular file")
            prior = AdmissionKeeperState.model_validate_json(latest.read_bytes())
        actual_prior = prior.state_id if prior is not None else None
        if actual_prior != expected_prior_state_id:
            raise AdmissionKeeperError(
                f"keeper state CAS conflict: expected {expected_prior_state_id!r}, "
                f"observed {actual_prior!r}"
            )
        immutable = self.states_root / f"{state.state_id[7:]}.json"
        payload = canonical_json_bytes(state.model_dump(mode="json")) + b"\n"
        if immutable.exists() and immutable.read_bytes() != payload:
            raise AdmissionKeeperError("keeper state content-address conflict")
        if not immutable.exists():
            _atomic_write(immutable, payload, exclusive=True)
        _atomic_write(latest, payload)
        return immutable

    def load_latest_state(self) -> AdmissionKeeperState | None:
        latest = self.root / "latest.json"
        if not latest.exists():
            return None
        if latest.is_symlink() or not latest.is_file():
            raise AdmissionKeeperError("keeper latest state must be a regular file")
        try:
            return AdmissionKeeperState.model_validate_json(latest.read_bytes())
        except ValidationError as exc:
            raise AdmissionKeeperError("keeper latest state is invalid") from exc

    def put_plan(self, plan: AdmissionKeeperRefreshPlan) -> Path:
        reject_secret_material(plan.model_dump(mode="json"), context="keeper plan")
        path = self.plans_root / f"{plan.plan_id[7:]}.json"
        payload = canonical_json_bytes(plan.model_dump(mode="json")) + b"\n"
        if path.exists():
            if path.is_symlink() or path.read_bytes() != payload:
                raise AdmissionKeeperError("keeper plan content-address conflict")
            return path
        _atomic_write(path, payload, exclusive=True)
        return path


def run_keeper_cycle(
    spec: AdmissionKeeperSpec,
    *,
    store: KeeperEvidenceStore,
    inbox_paths: Iterable[str | Path] = (),
    generated_at: datetime | None = None,
    renewal_margin_seconds: int = 60,
) -> AdmissionKeeperCycle:
    """Import owner nodes, plan incrementally, and CAS-publish one new state."""

    spec = materialize_keeper_spec(spec)
    now = _aware_utc(generated_at or datetime.now(timezone.utc))
    with store.cycle_lock():
        nodes = list(store.load_nodes())
        imported: list[str] = []
        for raw_path in sorted(Path(item) for item in inbox_paths):
            if raw_path.is_symlink() or not raw_path.is_file():
                raise AdmissionKeeperError("keeper inbox node must be a regular file")
            try:
                payload = raw_path.read_bytes()
                try:
                    node = AdmissionEvidenceNode.model_validate_json(payload)
                    assert_evidence_node(node, spec, nodes)
                except ValidationError:
                    statement = AdmissionEvidenceNodeStatement.model_validate_json(payload)
                    node = materialize_evidence_node(statement, spec, nodes)
            except (OSError, ValidationError) as exc:
                raise AdmissionKeeperError(f"invalid keeper inbox node {raw_path}") from exc
            store.put_node(node)
            if all(existing.node_id != node.node_id for existing in nodes):
                nodes.append(node)
                imported.append(node.node_id)
        prior = store.load_latest_state()
        plan = plan_keeper_refresh(
            spec,
            nodes=nodes,
            prior_state=prior,
            planned_at=now,
            renewal_margin_seconds=renewal_margin_seconds,
        )
        store.put_plan(plan)
        last_good_ref = prior.last_good_state_ref if prior is not None else None
        last_good_digest = prior.last_good_state_digest if prior is not None else None
        if prior is not None and prior.admission_current:
            last_good_ref = (
                f"keeper://{prior.organ_id}/{prior.contour_id}/state/{prior.state_id}"
            )
            last_good_digest = prior.state_id
        state = build_keeper_state(
            spec,
            nodes=nodes,
            prior_state=prior,
            updated_at=now,
            last_good_state_ref=last_good_ref,
            last_good_state_digest=last_good_digest,
        )
        store.publish_state(
            state,
            expected_prior_state_id=prior.state_id if prior is not None else None,
        )
        placeholder = AdmissionKeeperCycle(
            cycle_id="sha256:" + "0" * 64,
            generated_at=now,
            organ_id=spec.organ_id,
            contour_id=spec.contour_id,
            transaction_ref=spec.transaction_ref,
            imported_node_ids=tuple(imported),
            plan=plan,
            state=state,
        )
        return placeholder.model_copy(
            update={"cycle_id": canonical_digest(placeholder, exclude={"cycle_id"})}
        )


def _assert_node_statement(
    statement: AdmissionEvidenceNodeStatement,
    spec: AdmissionKeeperSpec,
    existing_nodes: tuple[AdmissionEvidenceNode, ...],
) -> None:
    if statement.spec_id != spec.spec_id:
        raise AdmissionKeeperError("keeper evidence references another spec")
    if (statement.organ_id, statement.contour_id) != (spec.organ_id, spec.contour_id):
        raise AdmissionKeeperError("keeper evidence crosses an organ contour")
    stage_spec = next((item for item in spec.stages if item.stage == statement.stage), None)
    if stage_spec is None:
        raise AdmissionKeeperError("keeper evidence stage is absent from the spec")
    if statement.stage_spec_digest != canonical_digest(stage_spec):
        raise AdmissionKeeperError("keeper evidence stage spec digest mismatch")
    if statement.owner != stage_spec.owner:
        raise AdmissionKeeperError("keeper evidence comes from the wrong owner")
    if statement.subject_digest != stage_spec.subject_digest:
        raise AdmissionKeeperError("keeper evidence subject digest mismatch")
    if statement.expires_at > spec.expires_at:
        raise AdmissionKeeperError("keeper evidence cannot outlive its spec")
    indexed = {item.node_id: item for item in existing_nodes}
    dependencies: list[str] = []
    for dependency_stage in stage_spec.dependency_stages:
        candidates = [
            item
            for item in existing_nodes
            if item.stage == dependency_stage and item.outcome == "passed"
        ]
        if not candidates:
            raise AdmissionKeeperError("keeper evidence dependency is absent")
        dependency = max(candidates, key=lambda item: (item.observed_at, item.node_id))
        dependencies.append(dependency.node_id)
    if tuple(dependencies) != statement.dependency_node_ids:
        raise AdmissionKeeperError("keeper evidence dependency chain mismatch")
    if any(node_id not in indexed for node_id in statement.dependency_node_ids):
        raise AdmissionKeeperError("keeper evidence references an unknown dependency")


def _assert_compatible_node(
    node: AdmissionEvidenceNode,
    spec: AdmissionKeeperSpec,
    existing_nodes: Iterable[AdmissionEvidenceNode],
) -> None:
    """Validate immutable evidence against a compatible newer keeper spec.

    Overall spec identity is intentionally not required here.  Unchanged stage
    input and exact dependency node identities are the reuse boundary.
    """

    if node.node_id != canonical_digest(node, exclude={"node_id"}):
        raise AdmissionKeeperError("keeper evidence node digest mismatch")
    if (node.organ_id, node.contour_id) != (spec.organ_id, spec.contour_id):
        raise AdmissionKeeperError("keeper evidence crosses an organ contour")
    stage_spec = next((item for item in spec.stages if item.stage == node.stage), None)
    if stage_spec is None:
        raise AdmissionKeeperError("keeper evidence stage is absent from the spec")
    if node.stage_spec_digest != canonical_digest(stage_spec):
        raise AdmissionKeeperError("keeper evidence stage input changed")
    if node.owner != stage_spec.owner or node.subject_digest != stage_spec.subject_digest:
        raise AdmissionKeeperError("keeper evidence owner or subject changed")
    indexed = {item.node_id: item for item in existing_nodes}
    dependency_stages = tuple(
        indexed[node_id].stage
        for node_id in node.dependency_node_ids
        if node_id in indexed
    )
    if len(dependency_stages) != len(node.dependency_node_ids):
        raise AdmissionKeeperError("keeper evidence dependency is absent")
    if dependency_stages != stage_spec.dependency_stages:
        raise AdmissionKeeperError("keeper evidence dependency topology changed")


def _latest_nodes(nodes: Iterable[AdmissionEvidenceNode]) -> dict[str, AdmissionEvidenceNode]:
    result: dict[str, AdmissionEvidenceNode] = {}
    for node in nodes:
        previous = result.get(node.stage)
        if previous is None or (node.observed_at, node.node_id) > (
            previous.observed_at,
            previous.node_id,
        ):
            result[node.stage] = node
    return result


def _classify_currentness(
    passed: set[str], blocked: bool, last_good_ref: str | None
) -> tuple[KeeperCurrentness, ...]:
    values: list[KeeperCurrentness] = []
    if {"process", "endpoint"}.issubset(passed):
        values.append("live")
    if {"owner_source", "package", "deployment", "process", "endpoint"}.issubset(passed):
        values.append("observed")
    if {"owner_grounding", "central_proof", "owner_acceptance", "rollback"}.issubset(passed):
        values.append("verified")
    if {"registry_admission", "consumer_observation"}.issubset(passed):
        values.append("admitted")
    if blocked:
        values.append("blocked")
        if passed:
            values.append("stale_readable")
    elif "admitted" not in values:
        values.append("candidate")
    if last_good_ref is not None:
        values.append("last_good")
    return tuple(dict.fromkeys(values))


def _atomic_write(path: Path, payload: bytes, *, exclusive: bool = False) -> None:
    if exclusive and path.exists():
        raise AdmissionKeeperError(f"refusing to replace immutable keeper file {path}")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if exclusive and path.exists():
            raise AdmissionKeeperError(f"refusing to replace immutable keeper file {path}")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AdmissionKeeperError("keeper timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)
