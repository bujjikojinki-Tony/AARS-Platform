from __future__ import annotations

from dataclasses import dataclass

from .config import RuntimeConfig
from .container import DependencyContainer
from .events import EventBus
from .health import HealthMonitor, HealthResult
from .lifecycle import LifecycleManager
from .loader import PluginLoader
from .plugin_manager import PluginManager
from .scheduler import Scheduler
from .storage import InMemoryStorage, StorageAdapter


@dataclass(frozen=True)
class RuntimePlatform:
    config: RuntimeConfig
    events: EventBus
    scheduler: Scheduler
    dependencies: DependencyContainer
    storage: StorageAdapter
    plugin_loader: PluginLoader
    plugins: PluginManager
    lifecycle: LifecycleManager
    health: HealthMonitor


def build_runtime(
    config: RuntimeConfig,
    storage: StorageAdapter | None = None,
) -> RuntimePlatform:
    events = EventBus()
    scheduler = Scheduler()
    dependencies = DependencyContainer()
    selected_storage = storage or InMemoryStorage()
    loader = PluginLoader(core_api_version=str(config.get("core.api_version", "1")))
    plugins = PluginManager(loader, events)
    lifecycle = LifecycleManager(plugins)
    health = HealthMonitor()
    health.register("runtime", lambda: HealthResult("runtime", "HEALTHY", "runtime initialized"))
    dependencies.register_instance("config", config)
    dependencies.register_instance("events", events)
    dependencies.register_instance("scheduler", scheduler)
    dependencies.register_instance("storage", selected_storage)
    dependencies.register_instance("plugins", plugins)
    return RuntimePlatform(
        config, events, scheduler, dependencies, selected_storage,
        loader, plugins, lifecycle, health,
    )

