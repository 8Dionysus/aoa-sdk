from __future__ import annotations

from builtins import list as builtin_list

from ..compatibility import load_surface
from ..compatibility.policy import SURFACE_COMPATIBILITY_RULES, _evaluate_data
from ..errors import IncompatibleSurfaceVersion, RecordNotFound, RepoNotFound, SurfaceNotFound
from ..loaders import load_json
from ..models import (
    StatsAutomationPipeline,
    StatsCoreSkillApplication,
    StatsForkCalibration,
    StatsGeneratedFrom,
    StatsObjectSummaryEntry,
    StatsRegroundingSignal,
    StatsRepeatedWindow,
    StatsRouteProgression,
    StatsSourceCoverageSummary,
    StatsSurfaceDetectionWindow,
    StatsSummarySurface,
)
from ..workspace.discovery import Workspace
from .regrounding import build_regrounding_signal, is_regrounding_intent, select_regrounding_surfaces


STATS_SURFACE_IDS = (
    "aoa-stats.object_summary.min",
    "aoa-stats.core_skill_application_summary.min",
    "aoa-stats.repeated_window_summary.min",
    "aoa-stats.route_progression_summary.min",
    "aoa-stats.fork_calibration_summary.min",
    "aoa-stats.automation_pipeline_summary.min",
    "aoa-stats.surface_detection_summary.min",
    "aoa-stats.source_coverage_summary.min",
    "aoa-stats.summary_surface_catalog.min",
)


class StatsAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def generated_from(self) -> StatsGeneratedFrom:
        data = self._load_stats_surface("aoa-stats.summary_surface_catalog.min")
        return StatsGeneratedFrom.model_validate(data.get("generated_from", {}))

    def object_summary(
        self,
        *,
        repo: str | None = None,
        kind: str | None = None,
        object_id: str | None = None,
    ) -> builtin_list[StatsObjectSummaryEntry]:
        entries = self._object_summary_entries()
        if repo is not None:
            entries = [entry for entry in entries if entry.object_ref.repo == repo]
        if kind is not None:
            entries = [entry for entry in entries if entry.object_ref.kind == kind]
        if object_id is not None:
            entries = [entry for entry in entries if entry.object_ref.id == object_id]
        return entries

    def core_skill_applications(
        self,
        *,
        kernel_id: str | None = None,
        skill_name: str | None = None,
    ) -> builtin_list[StatsCoreSkillApplication]:
        entries = self._core_skill_application_entries()
        if kernel_id is not None:
            entries = [entry for entry in entries if entry.kernel_id == kernel_id]
        if skill_name is not None:
            entries = [entry for entry in entries if entry.skill_name == skill_name]
        return entries

    def repeated_windows(
        self,
        *,
        window_date: str | None = None,
    ) -> builtin_list[StatsRepeatedWindow] | StatsRepeatedWindow:
        entries = self._repeated_window_entries()
        if window_date is None:
            return entries
        for entry in entries:
            if entry.window_date == window_date or entry.window_id == window_date:
                return entry
        raise RecordNotFound(f"Unknown stats repeated window: {window_date}")

    def route_progression(
        self,
        route_ref: str | None = None,
    ) -> builtin_list[StatsRouteProgression] | StatsRouteProgression:
        entries = self._route_progression_entries()
        if route_ref is None:
            return entries
        for entry in entries:
            if entry.route_ref == route_ref:
                return entry
        raise RecordNotFound(f"Unknown stats route progression: {route_ref}")

    def fork_calibration(
        self,
        route_ref: str | None = None,
    ) -> builtin_list[StatsForkCalibration] | StatsForkCalibration:
        entries = self._fork_calibration_entries()
        if route_ref is None:
            return entries
        for entry in entries:
            if entry.route_ref == route_ref:
                return entry
        raise RecordNotFound(f"Unknown stats fork calibration route: {route_ref}")

    def automation_pipelines(
        self,
        pipeline_ref: str | None = None,
    ) -> builtin_list[StatsAutomationPipeline] | StatsAutomationPipeline:
        entries = self._automation_pipeline_entries()
        if pipeline_ref is None:
            return entries
        for entry in entries:
            if entry.pipeline_ref == pipeline_ref:
                return entry
        raise RecordNotFound(f"Unknown stats automation pipeline: {pipeline_ref}")

    def summary_catalog(self) -> builtin_list[StatsSummarySurface]:
        data = self._load_stats_surface("aoa-stats.summary_surface_catalog.min")
        return [StatsSummarySurface.model_validate(item) for item in data.get("surfaces", [])]

    def source_coverage(self) -> StatsSourceCoverageSummary:
        data = self._load_stats_surface("aoa-stats.source_coverage_summary.min")
        return StatsSourceCoverageSummary.model_validate(data)

    def surface_profile(self, surface_name: str) -> StatsSummarySurface:
        for surface in self.summary_catalog():
            if surface.name == surface_name or surface.surface_ref == surface_name:
                return surface
        raise RecordNotFound(f"Unknown stats summary surface profile: {surface_name}")

    def regrounding_signal(
        self,
        surface_name: str,
        *,
        phase: str = "ingress",
        mutation_surface: str = "none",
    ) -> StatsRegroundingSignal:
        return build_regrounding_signal(
            surface=self.surface_profile(surface_name),
            coverage=self.source_coverage(),
            phase=phase,  # type: ignore[arg-type]
            mutation_surface=mutation_surface,  # type: ignore[arg-type]
        )

    def regrounding_signals_for_intent(
        self,
        *,
        intent_text: str,
        phase: str = "ingress",
        mutation_surface: str = "none",
    ) -> builtin_list[StatsRegroundingSignal]:
        if not is_regrounding_intent(intent_text):
            return []
        coverage = self.source_coverage()
        surfaces = select_regrounding_surfaces(
            surfaces=self.summary_catalog(),
            intent_text=intent_text,
        )
        return [
            build_regrounding_signal(
                surface=surface,
                coverage=coverage,
                phase=phase,  # type: ignore[arg-type]
                mutation_surface=mutation_surface,  # type: ignore[arg-type]
            )
            for surface in surfaces
        ]

    def surface_detection(
        self,
        *,
        window_date: str | None = None,
    ) -> builtin_list[StatsSurfaceDetectionWindow] | StatsSurfaceDetectionWindow:
        entries = self._surface_detection_entries()
        if window_date is None:
            return entries
        for entry in entries:
            if entry.window_date == window_date or entry.window_id == window_date:
                return entry
        raise RecordNotFound(f"Unknown stats surface detection window: {window_date}")

    def _object_summary_entries(self) -> builtin_list[StatsObjectSummaryEntry]:
        data = self._load_stats_surface("aoa-stats.object_summary.min")
        return [StatsObjectSummaryEntry.model_validate(item) for item in data.get("objects", [])]

    def _core_skill_application_entries(self) -> builtin_list[StatsCoreSkillApplication]:
        data = self._load_stats_surface("aoa-stats.core_skill_application_summary.min")
        return [StatsCoreSkillApplication.model_validate(item) for item in data.get("skills", [])]

    def _repeated_window_entries(self) -> builtin_list[StatsRepeatedWindow]:
        data = self._load_stats_surface("aoa-stats.repeated_window_summary.min")
        return [StatsRepeatedWindow.model_validate(item) for item in data.get("windows", [])]

    def _route_progression_entries(self) -> builtin_list[StatsRouteProgression]:
        data = self._load_stats_surface("aoa-stats.route_progression_summary.min")
        return [StatsRouteProgression.model_validate(item) for item in data.get("routes", [])]

    def _fork_calibration_entries(self) -> builtin_list[StatsForkCalibration]:
        data = self._load_stats_surface("aoa-stats.fork_calibration_summary.min")
        return [StatsForkCalibration.model_validate(item) for item in data.get("routes", [])]

    def _automation_pipeline_entries(self) -> builtin_list[StatsAutomationPipeline]:
        data = self._load_stats_surface("aoa-stats.automation_pipeline_summary.min")
        return [StatsAutomationPipeline.model_validate(item) for item in data.get("pipelines", [])]

    def _surface_detection_entries(self) -> builtin_list[StatsSurfaceDetectionWindow]:
        data = self._load_stats_surface("aoa-stats.surface_detection_summary.min")
        return [StatsSurfaceDetectionWindow.model_validate(item) for item in data.get("windows", [])]

    def _load_stats_surface(self, surface_id: str):
        rule = SURFACE_COMPATIBILITY_RULES[surface_id]
        relative_path = self._stats_relative_path(surface_id)
        try:
            data = load_json(self.workspace.surface_path(rule.repo, relative_path))
        except (RepoNotFound, SurfaceNotFound):
            data = load_surface(self.workspace, surface_id)
            return data
        result = _evaluate_data(rule, data, resolved_relative_path=relative_path)
        if not result.compatible:
            raise IncompatibleSurfaceVersion(
                f"Incompatible surface {surface_id}: {result.reason}"
            )
        return data

    def _stats_relative_path(self, surface_id: str) -> str:
        rule = SURFACE_COMPATIBILITY_RULES[surface_id]
        if self._use_live_stats_snapshot() and rule.preferred_relative_paths:
            return rule.preferred_relative_paths[0]
        return rule.relative_path

    def _use_live_stats_snapshot(self) -> bool:
        for surface_id in STATS_SURFACE_IDS:
            rule = SURFACE_COMPATIBILITY_RULES[surface_id]
            if not rule.preferred_relative_paths:
                continue
            try:
                path = self.workspace.surface_path(rule.repo, rule.preferred_relative_paths[0])
            except RepoNotFound:
                return False
            if not path.is_file():
                return False
        return True
