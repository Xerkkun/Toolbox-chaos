from __future__ import annotations

from dataclasses import dataclass
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
APP_DOI = '10.17605/OSF.IO/GQMJR'
APP_DOI_URL = 'https://doi.org/10.17605/OSF.IO/GQMJR'
ACADEMIC_NOTICE = (
    'Los resultados numericos deben interpretarse como evidencia computacional '
    'y no como prueba matematica automatica.'
)
RELEASE_API_ENV = 'CHAOS_TOOLBOX_RELEASES_API_URL'
UPDATE_CHECK_INTERVAL_DAYS = 7
DOCUMENTATION_ENTRY = 'docs/user-guide.md'


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _project_metadata() -> dict:
    pyproject = project_root() / 'pyproject.toml'
    with pyproject.open('rb') as handle:
        return tomllib.load(handle)


def project_version() -> str:
    try:
        return str(_project_metadata()['project']['version'])
    except Exception:
        return "0.1.0"


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
