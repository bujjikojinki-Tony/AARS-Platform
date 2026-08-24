from __future__ import annotations

import os
import platform
import plistlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .storage import MarketStore


LABEL_PREFIX = "com.aars.mil3"
JOB_NAMES = ("scheduler", "api", "health", "maintenance")
Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class MacOSDeploymentConfig:
    project_root: Path
    python_executable: Path
    runtime_root: Path
    api_port: int = 8765
    poll_seconds: int = 3600
    health_seconds: int = 300
    max_health_age_seconds: int = 7200
    retention_days: int = 30
    max_log_bytes: int = 10 * 1024 * 1024
    log_backups: int = 7

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_root", self.project_root.expanduser().resolve())
        object.__setattr__(
            self, "python_executable", self.python_executable.expanduser().resolve()
        )
        object.__setattr__(self, "runtime_root", self.runtime_root.expanduser().resolve())
        if not 1 <= self.api_port <= 65535:
            raise ValueError("api_port must be between 1 and 65535")
        for name in (
            "poll_seconds",
            "health_seconds",
            "max_health_age_seconds",
            "retention_days",
            "max_log_bytes",
            "log_backups",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")

    @property
    def data_dir(self) -> Path:
        return self.runtime_root / "data"

    @property
    def log_dir(self) -> Path:
        return self.runtime_root / "logs"

    @property
    def backup_dir(self) -> Path:
        return self.runtime_root / "backups"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "mil3_market.sqlite"


def _job(
    config: MacOSDeploymentConfig,
    name: str,
    arguments: list[str],
    **schedule: object,
) -> dict[str, object]:
    return {
        "Label": f"{LABEL_PREFIX}.{name}",
        "ProgramArguments": [str(config.python_executable), *arguments],
        "WorkingDirectory": str(config.project_root),
        "EnvironmentVariables": {"PYTHONUNBUFFERED": "1"},
        "StandardOutPath": str(config.log_dir / f"{name}.log"),
        "StandardErrorPath": str(config.log_dir / f"{name}-error.log"),
        "ProcessType": "Background",
        **schedule,
    }


def launch_agent_payloads(config: MacOSDeploymentConfig) -> dict[str, dict[str, object]]:
    root = config.project_root
    db = str(config.db_path)
    return {
        "scheduler": _job(
            config,
            "scheduler",
            [
                str(root / "run_scheduler.py"),
                "--db",
                db,
                "--poll-seconds",
                str(config.poll_seconds),
                "--max-cycles",
                "0",
            ],
            RunAtLoad=True,
            KeepAlive=True,
            ThrottleInterval=30,
        ),
        "api": _job(
            config,
            "api",
            [
                str(root / "run_api.py"),
                "--db",
                db,
                "--host",
                "127.0.0.1",
                "--port",
                str(config.api_port),
            ],
            RunAtLoad=True,
            KeepAlive=True,
            ThrottleInterval=30,
        ),
        "health": _job(
            config,
            "health",
            [
                str(root / "run_healthcheck.py"),
                "--db",
                db,
                "--max-cycle-age-seconds",
                str(config.max_health_age_seconds),
                "--max-candle-age-seconds",
                str(config.max_health_age_seconds),
            ],
            RunAtLoad=True,
            StartInterval=config.health_seconds,
        ),
        "maintenance": _job(
            config,
            "maintenance",
            [
                str(root / "run_backup.py"),
                "--db",
                db,
                "--backup-dir",
                str(config.backup_dir),
                "--retention-days",
                str(config.retention_days),
                "--log-dir",
                str(config.log_dir),
                "--max-log-bytes",
                str(config.max_log_bytes),
                "--log-backups",
                str(config.log_backups),
            ],
            RunAtLoad=False,
            StartCalendarInterval={"Hour": 2, "Minute": 15},
            LowPriorityIO=True,
        ),
    }


def prepare_runtime(config: MacOSDeploymentConfig) -> None:
    required_scripts = (
        "run_scheduler.py",
        "run_api.py",
        "run_healthcheck.py",
        "run_backup.py",
    )
    missing = [name for name in required_scripts if not (config.project_root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"project root is missing: {', '.join(missing)}")
    if not config.python_executable.is_file():
        raise FileNotFoundError(f"Python executable not found: {config.python_executable}")
    for directory in (config.runtime_root, config.data_dir, config.log_dir, config.backup_dir):
        directory.mkdir(parents=True, exist_ok=True)
    MarketStore(config.db_path).init_db()


def render_launch_agents(
    config: MacOSDeploymentConfig, agents_dir: str | Path
) -> list[Path]:
    destination = Path(agents_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, payload in launch_agent_payloads(config).items():
        path = destination / f"{LABEL_PREFIX}.{name}.plist"
        temporary = path.with_suffix(".plist.tmp")
        temporary.write_bytes(plistlib.dumps(payload, sort_keys=True))
        os.replace(temporary, path)
        path.chmod(0o600)
        written.append(path)
    return written


def install_launch_agents(
    config: MacOSDeploymentConfig,
    agents_dir: str | Path,
    *,
    load: bool = True,
    runner: Runner = subprocess.run,
) -> dict[str, object]:
    if load and platform.system() != "Darwin":
        raise RuntimeError("launchd loading is only supported on macOS")
    prepare_runtime(config)
    paths = render_launch_agents(config, agents_dir)
    loaded: list[str] = []
    if load:
        domain = f"gui/{os.getuid()}"
        for path in paths:
            label = path.stem
            runner(
                ["launchctl", "bootout", f"{domain}/{label}"],
                check=False,
                capture_output=True,
                text=True,
            )
            runner(
                ["launchctl", "bootstrap", domain, str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
            loaded.append(label)
    return {
        "execution_mode": "PAPER_ONLY",
        "runtime_root": str(config.runtime_root),
        "database": str(config.db_path),
        "plists": [str(path) for path in paths],
        "loaded": loaded,
    }


def uninstall_launch_agents(
    agents_dir: str | Path,
    *,
    unload: bool = True,
    runner: Runner = subprocess.run,
) -> dict[str, object]:
    if unload and platform.system() != "Darwin":
        raise RuntimeError("launchd unloading is only supported on macOS")
    destination = Path(agents_dir).expanduser().resolve()
    domain = f"gui/{os.getuid()}"
    removed: list[str] = []
    for name in JOB_NAMES:
        label = f"{LABEL_PREFIX}.{name}"
        if unload:
            runner(
                ["launchctl", "bootout", f"{domain}/{label}"],
                check=False,
                capture_output=True,
                text=True,
            )
        path = destination / f"{label}.plist"
        if path.exists():
            path.unlink()
            removed.append(str(path))
    return {
        "execution_mode": "PAPER_ONLY",
        "removed_plists": removed,
        "runtime_data_preserved": True,
    }


def launch_agent_status(runner: Runner = subprocess.run) -> dict[str, object]:
    if platform.system() != "Darwin":
        raise RuntimeError("launchd status is only supported on macOS")
    domain = f"gui/{os.getuid()}"
    services: dict[str, dict[str, object]] = {}
    for name in JOB_NAMES:
        label = f"{LABEL_PREFIX}.{name}"
        result = runner(
            ["launchctl", "print", f"{domain}/{label}"],
            check=False,
            capture_output=True,
            text=True,
        )
        services[name] = {
            "loaded": result.returncode == 0,
            "detail": result.stdout.strip() if result.returncode == 0 else result.stderr.strip(),
        }
    return {"execution_mode": "PAPER_ONLY", "services": services}
