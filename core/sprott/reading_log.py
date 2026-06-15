"""reading_log.py — diario de lectura local del Explorador Sprott.

Persiste las marcas y notas que el usuario hace mientras lee el libro físico
y carga los códigos del .DIC local. El JSON se guarda fuera del repositorio,
en la carpeta de datos del usuario.

No redistribuye ni copia ningún archivo ni texto del libro original.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


# Marcas válidas para una entrada de lectura
READING_MARKS: tuple[str, ...] = (
    'visto',
    'favorito',
    'pendiente',
    'no_coincide',
    'requiere_especial',
)

# Etiquetas legibles para cada marca
MARK_LABELS: dict[str, str] = {
    'visto': '✓ Visto',
    'favorito': '★ Favorito',
    'pendiente': '⏳ Pendiente',
    'no_coincide': '✗ No coincide',
    'requiere_especial': '🔧 Req. especial',
}

# Iconos cortos para mostrar en la tabla
MARK_ICONS: dict[str, str] = {
    'visto': '✓',
    'favorito': '★',
    'pendiente': '⏳',
    'no_coincide': '✗',
    'requiere_especial': '🔧',
}

# Colores de fondo (CSS hex) por marca dominante
MARK_ROW_COLORS: dict[str, str] = {
    'no_coincide': '#fce4ec',
    'pendiente': '#fff3e0',
    'favorito': '#fffde7',
    'visto': '#e8f5e9',
    'requiere_especial': '#f3e5f5',
}

# Prioridad de color: si hay varias marcas se usa la de mayor prioridad
MARK_COLOR_PRIORITY: tuple[str, ...] = (
    'no_coincide', 'pendiente', 'requiere_especial', 'favorito', 'visto'
)


def reading_log_path() -> Path:
    """Ruta del JSON de marcas de lectura, fuera del repositorio."""
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA') or Path.home() / 'AppData' / 'Roaming')
        return base / 'Chaos Toolbox' / 'book_reading_log.json'
    return Path.home() / '.chaos_toolbox' / 'book_reading_log.json'


def load_reading_log(path: str | Path | None = None) -> dict:
    """Carga el log completo. Devuelve dict vacío si no existe o hay error."""
    target = Path(path) if path else reading_log_path()
    if not target.exists():
        return {}
    with target.open('r', encoding='utf-8') as handle:
        try:
            data = json.load(handle)
        except Exception:
            return {}
    return data if isinstance(data, dict) else {}


def save_reading_log(log: dict, path: str | Path | None = None) -> Path:
    """Sobreescribe el JSON del log. Crea el directorio si no existe."""
    target = Path(path) if path else reading_log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', encoding='utf-8') as handle:
        json.dump(log, handle, indent=2, ensure_ascii=False)
    return target


def entry_key(source_name: str, line: int) -> str:
    """Clave única para una entrada: 'BOOKFIGS.DIC:42'."""
    return f'{source_name}:{int(line)}'


def get_entry(log: dict, key: str) -> dict:
    """Obtiene una entrada del log, creándola vacía si no existe."""
    if key not in log:
        log[key] = {'marks': [], 'note': '', 'last_updated': ''}
    return log[key]


def set_mark(log: dict, key: str, mark: str, active: bool) -> dict:
    """Activa o desactiva una marca para la entrada dada.

    Parameters
    ----------
    log:    el log completo (se modifica in-place y se devuelve)
    key:    clave de la entrada
    mark:   nombre de la marca (debe estar en READING_MARKS)
    active: True = añadir, False = quitar
    """
    if mark not in READING_MARKS:
        return log
    entry = get_entry(log, key)
    marks: list[str] = list(entry.get('marks', []))
    if active and mark not in marks:
        marks.append(mark)
    elif not active and mark in marks:
        marks.remove(mark)
    entry['marks'] = marks
    entry['last_updated'] = datetime.now(timezone.utc).isoformat()
    log[key] = entry
    return log


def set_note(log: dict, key: str, note: str) -> dict:
    """Guarda una nota de texto libre para la entrada."""
    entry = get_entry(log, key)
    entry['note'] = str(note)
    entry['last_updated'] = datetime.now(timezone.utc).isoformat()
    log[key] = entry
    return log


def set_code(log: dict, key: str, code: str, source_name: str, line: int) -> dict:
    """Actualiza los metadatos de código de la entrada."""
    entry = get_entry(log, key)
    entry['code'] = str(code)
    entry['source_name'] = str(source_name)
    entry['line'] = int(line)
    entry['last_updated'] = datetime.now(timezone.utc).isoformat()
    log[key] = entry
    return log


def dominant_color(marks: list[str]) -> str | None:
    """Devuelve el color CSS de la marca dominante, o None si no hay marcas."""
    for mark in MARK_COLOR_PRIORITY:
        if mark in marks:
            return MARK_ROW_COLORS.get(mark)
    return None


def marks_icons_text(marks: list[str]) -> str:
    """Convierte lista de marcas a cadena de iconos para mostrar en tabla."""
    return ' '.join(MARK_ICONS[m] for m in marks if m in MARK_ICONS)
