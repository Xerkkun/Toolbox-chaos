from __future__ import annotations

import struct
import warnings
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, UnidentifiedImageError


PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
DEFAULT_MAX_IMAGE_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_IMAGE_PIXELS = 64_000_000


class ImageSecurityError(ValueError):
    """Raised when an image is not a confined, valid PNG resource."""


def _is_link_like(path: Path) -> bool:
    is_junction = getattr(path, 'is_junction', lambda: False)
    return path.is_symlink() or bool(is_junction())


def validate_png_file(
    path: str | Path,
    *,
    max_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
    max_pixels: int = DEFAULT_MAX_IMAGE_PIXELS,
) -> Path:
    """Validate one regular PNG without handing another format to Qt."""

    candidate = Path(path)
    if candidate.suffix.casefold() != '.png':
        raise ImageSecurityError('Solo se admiten imagenes PNG.')
    if not candidate.is_file() or _is_link_like(candidate):
        raise ImageSecurityError('La imagen debe ser un archivo regular sin enlaces.')
    size = candidate.stat().st_size
    if size <= len(PNG_SIGNATURE) or size > int(max_bytes):
        raise ImageSecurityError('La imagen PNG tiene un tamano no permitido.')

    with candidate.open('rb') as handle:
        header = handle.read(24)
    if not header.startswith(PNG_SIGNATURE):
        raise ImageSecurityError('La extension PNG no coincide con la firma del archivo.')
    if len(header) < 24 or header[12:16] != b'IHDR':
        raise ImageSecurityError('La imagen PNG no contiene una cabecera IHDR valida.')
    width, height = struct.unpack('>II', header[16:24])
    if width <= 0 or height <= 0 or width * height > int(max_pixels):
        raise ImageSecurityError('Las dimensiones de la imagen PNG no estan permitidas.')

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(candidate) as image:
                if image.format != 'PNG' or image.size != (width, height):
                    raise ImageSecurityError('El decodificador no reconoce un PNG coherente.')
                image.verify()
    except ImageSecurityError:
        raise
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombWarning) as exc:
        raise ImageSecurityError('La imagen PNG no se puede decodificar de forma segura.') from exc
    return candidate


def confined_png(
    root: str | Path,
    relative_name: object,
    *,
    max_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
    max_pixels: int = DEFAULT_MAX_IMAGE_PIXELS,
) -> Path:
    """Resolve a relative PNG below *root* and reject URLs and link traversal."""

    if not isinstance(relative_name, str) or not relative_name.strip():
        raise ImageSecurityError('La ruta de imagen esta vacia.')
    raw_name = relative_name.strip()
    parsed = urlsplit(raw_name)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ImageSecurityError('Las imagenes remotas o con URI no estan permitidas.')

    relative = Path(raw_name)
    if relative.is_absolute() or any(part in {'', '.', '..'} for part in relative.parts):
        raise ImageSecurityError('La imagen debe usar una ruta relativa confinada.')

    base = Path(root).expanduser().resolve(strict=True)
    unresolved = base / relative
    current = base
    for part in relative.parts:
        current = current / part
        if current.exists() and _is_link_like(current):
            raise ImageSecurityError('Las imagenes enlazadas no estan permitidas.')
    resolved = unresolved.resolve(strict=True)
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ImageSecurityError('La imagen intenta salir de su raiz autorizada.') from exc
    return validate_png_file(
        resolved,
        max_bytes=max_bytes,
        max_pixels=max_pixels,
    )
