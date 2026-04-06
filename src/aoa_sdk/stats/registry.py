from __future__ import annotations

from builtins import list as builtin_list

from ..compatibility import load_surface
from ..errors import RecordNotFound
from ..models import (
    StatsAutomationPipeline,
    StatsCoreSkillApplication,
    StatsForkCalibration,
    StatsGeneratedFrom,
    StatsObjectSummaryEntry,
    StatsRepeatedWindow,
    StatsRouteProgression,
    StatsSummarySurface,
)
from ..workspace.discovery import Workspace


class StatsAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def generated_from(self) -> StatsGeneratedFrom:
        data = load_surface(self.workspace, "aoa-stats.summary_surface_catalog.min")
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
        data = load_surface(self.workspace, "aoa-stats.summary_surface_catalog.min")
        return [StatsSummarySurface.model_validate(item) for item in data.get("surfaces", [])]

    def _object_summary_entries(self) -> builtin_list[StatsObjectSummaryEntry]:
        data = load_surface(self.workspace, "aoa-stats.object_summary.min")
        return [StatsObjectSummaryEntry.model_validate(item) for item in data.get("objects", [])]

    def _core_skill_application_entries(self) -> builtin_list[StatsCoreSkillApplication]:
        data = load_surface(self.workspace, "aoa-stats.core_skill_application_summary.min")
        return [StatsCoreSkillApplication.model_validate(item) for item in data.get("skills", [])]

    def _repeated_window_entries(self) -> builtin_list[StatsRepeatedWindow]:
        data = load_surface(self.workspace, "aoa-stats.repeated_window_summary.min")
        return [StatsRepeatedWindow.model_validate(item) for item in data.get("windows", [])]

    def _route_progression_entries(self) -> builtin_list[StatsRouteProgression]:
        data = load_surface(self.workspace, "aoa-stats.route_progression_summary.min")
        return [StatsRouteProgression.model_validate(item) for item in data.get("routes", [])]

    def _fork_calibration_entries(self) -> builtin_list[StatsForkCalibration]:
        data = load_surface(self.workspace, "aoa-stats.fork_calibration_summary.min")
        return [StatsForkCalibration.model_validate(item) for item in data.get("routes", [])]

    def _automation_pipeline_entries(self) -> builtin_list[StatsAutomationPipeline]:
        data = load_surface(self.workspace, "aoa-stats.automation_pipeline_summary.min")
        return [StatsAutomationPipeline.model_validate(item) for item in data.get("pipelines", [])]
