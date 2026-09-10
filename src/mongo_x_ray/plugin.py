"""
Copyright (c) 2026 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.

Plugin discovery and shared command-line infrastructure.

Each analysis module (log, ftdc, gmd, healthcheck, ...) is a *command
plugin* that the CLI discovers at startup. Built-in plugins ship with the
core and are registered explicitly (so the CLI works from a source
checkout); additional ``mongo-x-ray-*`` distributions register through the
``mongo_x_ray.plugins`` entry-point group.
"""

import argparse
import logging
import os
import re
import shutil
import webbrowser
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path

from mongo_x_ray.utils import env, green

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "mongo_x_ray.plugins"


class Plugin(ABC):
    """A command plugin: one CLI subcommand that runs one analysis.

    Subclasses set the ``name``/``help``/``description``/``epilog`` class
    attributes, optionally override :meth:`add_arguments` to declare their
    CLI flags, and implement :meth:`run`. ``aliases`` lists extra subcommand
    names that invoke the same plugin (e.g. ``["hc"]`` for ``healthcheck``).
    ``distribution`` is the plugin's installed distribution name, used to
    report its own version via ``x-ray <name> --version``.
    """

    name: str = ""
    help: str = ""
    description: str = ""
    epilog: str = ""
    aliases: list[str] = []
    distribution: str = ""

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add this plugin's arguments to its subcommand parser."""

    @abstractmethod
    def run(self, args: argparse.Namespace) -> int:
        """Execute the plugin command and return the process exit code."""

    def version(self) -> str:
        """Return the installed version of this plugin's distribution."""
        try:
            return pkg_version(self.distribution)
        except PackageNotFoundError:
            return "development"


# --- shared command helpers -------------------------------------------------


def discover_paths(root: Path, glob_pattern: str) -> list[Path]:
    """Recursively search *root* for directories containing files matching *glob_pattern*.

    Returns a list of directory paths, sorted by depth (shallowest first).
    """
    found: dict[str, Path] = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            if Path(filename).match(glob_pattern):
                found[str(dirpath)] = Path(dirpath)
                break  # one match per directory is enough
    return sorted(found.values(), key=lambda p: (len(p.relative_to(root).parts), str(p)))


_ILLEGAL_FILENAME_RE = re.compile(r'[<>:"/\\|?*]')


def _sanitize_filename(name: str) -> str:
    """Replace characters illegal in Windows filenames with underscores."""
    return _ILLEGAL_FILENAME_RE.sub("_", name).strip(". ")


def rename_with_hostname(batch_folder: str, framework) -> str:
    """Rename *batch_folder* to include the plugin name as a prefix.

    Returns the final folder path (renamed or original). In production the
    folder is renamed to ``<plugin>-<hostname>-<name>`` (or ``<plugin>-<name>``
    when the framework knows no hostname), where *plugin* is the framework's
    ``template_module`` (e.g. ``log``) — so it is always clear which plugin
    produced the report, and with ``--discover`` which run it belongs to.
    """
    if env == "development":
        return batch_folder
    batch_path = Path(batch_folder)
    if not batch_path.is_dir():
        return batch_folder
    plugin = _sanitize_filename(getattr(framework, "template_module", "") or "") or "x-ray"
    hostname = getattr(framework, "hostname", None)
    if hostname:
        safe_hostname = _sanitize_filename(hostname)
        if safe_hostname:
            plugin = f"{plugin}-{safe_hostname}"
    if batch_path.name.startswith(plugin + "-"):
        return batch_folder  # already prefixed
    new_path = batch_path.parent / f"{plugin}-{batch_path.name}"
    shutil.move(str(batch_path), str(new_path))
    logger.info("Renamed output folder to: %s", green(new_path.name))
    return str(new_path)


def utc_iso_datetime(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and normalize it to UTC."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def sample_rate(value: str) -> float:
    """Parse a sampling rate in the interval (0, 1]."""
    try:
        rate = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid sample rate: {value}") from exc
    if not 0 < rate <= 1:
        raise argparse.ArgumentTypeError("sample rate must be greater than 0 and at most 1")
    return rate


def open_report(framework, output_folder: str, fmt: str, no_browser: bool) -> None:
    """Rename the batch folder with the hostname and open the report in a browser."""
    batch_folder = str(framework._get_output_folder(output_folder))
    final_folder = rename_with_hostname(batch_folder, framework)
    if fmt in {"html", "pdf"} and not no_browser:
        html_file = Path(final_folder) / "report.html"
        if html_file.exists():
            webbrowser.open(f"file://{html_file.resolve()}")
