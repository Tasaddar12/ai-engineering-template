"""Setuptools backend that derives packaged assets from repository-root sources.

The temporary ``src/_assets`` tree exists only while a wheel is assembled. Editable
installs resolve the authored root assets directly, and sdists carry those roots via
``MANIFEST.in`` so a later wheel build can derive the same package data.
"""

from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from setuptools import build_meta as _setuptools

_ROOT = Path(__file__).resolve().parent.parent
_STAGE = Path(__file__).resolve().parent / "_assets"
_DIRECTORIES = ("agents", "templates", "workflows", "constraints")


def _require_sources() -> None:
    missing = [name for name in (*_DIRECTORIES, "framework.yaml") if not (_ROOT / name).exists()]
    if missing:
        raise RuntimeError(f"Cannot package missing root assets: {', '.join(missing)}")


@contextmanager
def _staged_assets() -> Iterator[None]:
    _require_sources()
    if _STAGE.exists():
        raise RuntimeError("src/_assets already exists; packaged assets must be derived, not authored")
    try:
        _STAGE.mkdir()
        for name in _DIRECTORIES:
            shutil.copytree(_ROOT / name, _STAGE / name)
        shutil.copy2(_ROOT / "framework.yaml", _STAGE / "framework.yaml")
        yield
    finally:
        if _STAGE.exists():
            shutil.rmtree(_STAGE)


def build_wheel(wheel_directory: str, config_settings=None, metadata_directory=None) -> str:
    with _staged_assets():
        return _setuptools.build_wheel(wheel_directory, config_settings, metadata_directory)


def build_editable(wheel_directory: str, config_settings=None, metadata_directory=None) -> str:
    return _setuptools.build_editable(wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory: str, config_settings=None) -> str:
    _require_sources()
    return _setuptools.build_sdist(sdist_directory, config_settings)


def prepare_metadata_for_build_wheel(metadata_directory: str, config_settings=None) -> str:
    return _setuptools.prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def get_requires_for_build_wheel(config_settings=None) -> list[str]:
    return _setuptools.get_requires_for_build_wheel(config_settings)


def get_requires_for_build_editable(config_settings=None) -> list[str]:
    return _setuptools.get_requires_for_build_editable(config_settings)


def get_requires_for_build_sdist(config_settings=None) -> list[str]:
    return _setuptools.get_requires_for_build_sdist(config_settings)
