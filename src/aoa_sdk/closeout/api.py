from __future__ import annotations

from ..workspace.discovery import Workspace
from .filesystem import (
    _archive_manifest as _archive_manifest_impl,
    _derive_closeout_id as _derive_closeout_id_impl,
    _latest_path as _latest_path_impl,
    _resolve_existing_path as _resolve_existing_path_impl,
    _resolve_input_paths as _resolve_input_paths_impl,
    _resolve_optional_paths as _resolve_optional_paths_impl,
    _resolve_queue_dir as _resolve_queue_dir_impl,
    _safe_closeout_filename as _safe_closeout_filename_impl,
    _unique_paths as _unique_paths_impl,
    _unique_strings as _unique_strings_impl,
    default_closeout_root as default_closeout_root_impl,
    default_queue_paths as default_queue_paths_impl,
)
from .followthrough import (
    _build_harvest_follow_through_briefs as _build_harvest_follow_through_briefs_impl,
    _build_kernel_next_step_brief as _build_kernel_next_step_brief_impl,
    _build_owner_follow_through_briefs as _build_owner_follow_through_briefs_impl,
    _build_quest_follow_through_briefs as _build_quest_follow_through_briefs_impl,
    _build_workflow_follow_through_briefs as _build_workflow_follow_through_briefs_impl,
    _collect_current_detail_event_kinds as _collect_current_detail_event_kinds_impl,
    _collect_current_session_skill_names as _collect_current_session_skill_names_impl,
    _invoke_core_skill_brief as _invoke_core_skill_brief_impl,
    _latest_detail_receipt as _latest_detail_receipt_impl,
    _load_kernel_usage_counts as _load_kernel_usage_counts_impl,
    _load_quest_unit_name as _load_quest_unit_name_impl,
    _owner_follow_through_key as _owner_follow_through_key_impl,
    _resolve_kernel_next_step as _resolve_kernel_next_step_impl,
    _write_owner_handoff as _write_owner_handoff_impl,
)
from .manifests import (
    _validate_build_request as _validate_build_request_impl,
    _validate_manifest as _validate_manifest_impl,
    build_manifest as build_manifest_impl,
    load_build_request as load_build_request_impl,
    load_manifest as load_manifest_impl,
    submit_reviewed as submit_reviewed_impl,
)
from .publishers import (
    _parse_named_path as _parse_named_path_impl,
    _parse_publish_stdout as _parse_publish_stdout_impl,
    _parse_refresh_stdout as _parse_refresh_stdout_impl,
    _run_command as _run_command_impl,
    _run_publisher_batch as _run_publisher_batch_impl,
    _run_stats_refresh as _run_stats_refresh_impl,
    _skipped_stats_refresh as _skipped_stats_refresh_impl,
)
from .queue import (
    enqueue as enqueue_impl,
    process_inbox as process_inbox_impl,
    status as status_impl,
)
from .receipts import (
    _collect_receipt_paths as _collect_receipt_paths_impl,
    _extract_evidence_ref_strings as _extract_evidence_ref_strings_impl,
    _load_kernel_receipt_batches as _load_kernel_receipt_batches_impl,
    _load_receipt_file as _load_receipt_file_impl,
    _publisher_for_receipt_path as _publisher_for_receipt_path_impl,
    _resolve_evidence_path as _resolve_evidence_path_impl,
    _resolve_receipt_evidence_paths as _resolve_receipt_evidence_paths_impl,
)
from .runner import run as run_impl


class CloseoutAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    load_build_request = load_build_request_impl
    submit_reviewed = submit_reviewed_impl
    load_manifest = load_manifest_impl
    build_manifest = build_manifest_impl
    run = run_impl
    enqueue = enqueue_impl
    process_inbox = process_inbox_impl
    status = status_impl
    default_closeout_root = default_closeout_root_impl
    default_queue_paths = default_queue_paths_impl

    _validate_build_request = _validate_build_request_impl
    _validate_manifest = _validate_manifest_impl
    _resolve_queue_dir = _resolve_queue_dir_impl
    _resolve_existing_path = _resolve_existing_path_impl
    _collect_receipt_paths = _collect_receipt_paths_impl
    _publisher_for_receipt_path = _publisher_for_receipt_path_impl
    _load_receipt_file = _load_receipt_file_impl
    _resolve_input_paths = _resolve_input_paths_impl
    _resolve_optional_paths = _resolve_optional_paths_impl
    _run_publisher_batch = _run_publisher_batch_impl
    _run_stats_refresh = _run_stats_refresh_impl
    _build_kernel_next_step_brief = _build_kernel_next_step_brief_impl
    _build_owner_follow_through_briefs = _build_owner_follow_through_briefs_impl
    _build_workflow_follow_through_briefs = _build_workflow_follow_through_briefs_impl
    _build_harvest_follow_through_briefs = _build_harvest_follow_through_briefs_impl
    _build_quest_follow_through_briefs = _build_quest_follow_through_briefs_impl
    _load_quest_unit_name = _load_quest_unit_name_impl
    _owner_follow_through_key = _owner_follow_through_key_impl
    _resolve_receipt_evidence_paths = _resolve_receipt_evidence_paths_impl
    _extract_evidence_ref_strings = _extract_evidence_ref_strings_impl
    _resolve_evidence_path = _resolve_evidence_path_impl
    _write_owner_handoff = _write_owner_handoff_impl
    _skipped_stats_refresh = _skipped_stats_refresh_impl
    _run_command = _run_command_impl
    _parse_publish_stdout = _parse_publish_stdout_impl
    _parse_refresh_stdout = _parse_refresh_stdout_impl
    _parse_named_path = _parse_named_path_impl
    _load_kernel_receipt_batches = _load_kernel_receipt_batches_impl
    _collect_current_detail_event_kinds = _collect_current_detail_event_kinds_impl
    _collect_current_session_skill_names = _collect_current_session_skill_names_impl
    _load_kernel_usage_counts = _load_kernel_usage_counts_impl
    _resolve_kernel_next_step = _resolve_kernel_next_step_impl
    _invoke_core_skill_brief = _invoke_core_skill_brief_impl
    _latest_detail_receipt = _latest_detail_receipt_impl
    _archive_manifest = _archive_manifest_impl
    _latest_path = _latest_path_impl
    _safe_closeout_filename = _safe_closeout_filename_impl
    _unique_strings = _unique_strings_impl
    _unique_paths = _unique_paths_impl
    _derive_closeout_id = _derive_closeout_id_impl
