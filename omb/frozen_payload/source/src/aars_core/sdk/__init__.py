"""Stable public interfaces for AARS-ROS plugin authors."""

from aars_core.contracts import EvidenceProvider, KnowledgeAdapter, MemoryAdapter, ObservationProvider, OutcomeValidator
from aars_core.models import Decision, Evidence, EvidenceItem, Knowledge, Lesson, Memory, Observation, Outcome, Provenance
from aars_core.plugin import PluginManifest, ResearchPlugin
from aars_core.runtime import (
    ConfigLoader, DependencyContainer, Event, EventBus, HealthMonitor, HealthResult,
    LifecycleCase, LifecycleManager, PluginLoader, PluginManager, PluginStatus,
    PluginValidationError, RuntimeConfig, RuntimePlatform, ScheduledTask, Scheduler,
    StorageAdapter, build_runtime,
)

CORE_API_VERSION = "1"

__all__ = [
    "CORE_API_VERSION", "ConfigLoader", "Decision", "DependencyContainer", "Event",
    "EventBus", "Evidence", "EvidenceItem", "EvidenceProvider", "HealthMonitor",
    "HealthResult", "Knowledge", "KnowledgeAdapter", "Lesson", "LifecycleCase",
    "LifecycleManager", "Memory", "MemoryAdapter", "Observation", "ObservationProvider",
    "Outcome", "OutcomeValidator", "PluginLoader", "PluginManager", "PluginManifest",
    "PluginStatus", "PluginValidationError", "Provenance", "ResearchPlugin",
    "RuntimeConfig", "RuntimePlatform", "ScheduledTask", "Scheduler", "StorageAdapter",
    "build_runtime",
]
