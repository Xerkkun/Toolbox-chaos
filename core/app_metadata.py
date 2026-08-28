from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version as distribution_version
from pathlib import Path
import tomllib


APP_NAME = 'Chaos Toolbox'
APP_SLUG = 'chaos-toolbox'
APP_DESCRIPTION = (
    'Toolbox de sistemas caoticos, analisis numerico, visualizacion y '
    'exploracion de atractores.'
)
APP_DEVELOPER = 'Maria Fernanda Moreno Lopez'
APP_ORGANIZATION = 'Maria Fernanda Moreno Lopez'
APP_BRAND = 'Fyskode'
APP_AUTHOR_DISPLAY = 'Maria Fernanda Moreno Lopez (Fer Moreno)'
APP_LICENSE = 'MIT'
APP_YEAR = '2026'
APP_RELEASE_STATUS = 'stable release'
APP_RELEASE_DATE = '2026-08-28'
APP_DOI = '10.17605/OSF.IO/GQMJR'
APP_DOI_URL = 'https://doi.org/10.17605/OSF.IO/GQMJR'
ACADEMIC_NOTICE = (
    'Los resultados numericos deben interpretarse como evidencia computacional '
    'y no como prueba matematica automatica.'
)
RELEASE_API_ENV = 'CHAOS_TOOLBOX_RELEASES_API_URL'
DEFAULT_RELEASE_API_URL = (
    'https://api.github.com/repos/Xerkkun/toolbox-chaos/releases/latest'
)
UPDATE_CHECK_INTERVAL_DAYS = 7
DOCUMENTATION_ENTRY = (
    'resources/bundled/docs/manual_usuario_toolbox_chaos.pdf'
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _project_metadata() -> dict:
    pyproject = project_root() / 'pyproject.toml'
    with pyproject.open('rb') as handle:
        return tomllib.load(handle)


def project_version() -> str:
    pyproject = project_root() / 'pyproject.toml'
    if pyproject.is_file():
        metadata = _project_metadata()
        try:
            return str(metadata['project']['version'])
        except (KeyError, TypeError) as exc:
            raise RuntimeError(
                "pyproject.toml no contiene project.version."
            ) from exc
    try:
        return distribution_version(APP_SLUG)
    except PackageNotFoundError as exc:
        raise RuntimeError(
            "No se pudo determinar la version instalada de Chaos Toolbox."
        ) from exc


APP_VERSION = project_version()


@dataclass(frozen=True)
class AppMetadata:
    name: str = APP_NAME
    version: str = APP_VERSION
    slug: str = APP_SLUG
    developer: str = APP_DEVELOPER
    license: str = APP_LICENSE
    year: str = APP_YEAR
    description: str = APP_DESCRIPTION
    academic_notice: str = ACADEMIC_NOTICE


def artifact_basename(platform_tag: str, suffix: str) -> str:
    clean_suffix = suffix if suffix.startswith('.') else f'.{suffix}'
    return f'{APP_SLUG}-v{APP_VERSION}-{platform_tag}{clean_suffix}'
