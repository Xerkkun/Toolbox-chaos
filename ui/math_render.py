from __future__ import annotations

import hashlib
import html
import os
import re
import tempfile
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image

_CACHE_DIR = Path(os.environ.get('CHAOS_MATH_CACHE', tempfile.gettempdir())) / 'chaos_toolbox_math_cache'
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def render_math_to_path(expression: str, *, size: int = 14, color: str = 'black') -> str:
    """Render a TeX-like math expression to a cached PNG file and return its path.

    Falls back to plain text rendering if MathText parsing fails, so the GUI does
    not crash because of a malformed or unsupported expression.
    """
    key = hashlib.sha256(f'{expression}|{size}|{color}'.encode('utf-8')).hexdigest()
    out_path = _CACHE_DIR / f'{key}.png'
    if not out_path.exists():
        prop = FontProperties(size=size)
        try:
            math_to_image(expression, str(out_path), prop=prop, dpi=180, format='png', color=color)
        except Exception:
            fig = Figure(figsize=(8, 0.55), dpi=180)
            FigureCanvasAgg(fig)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.axis('off')
            plain = expression.strip()
            if plain.startswith('$') and plain.endswith('$') and len(plain) >= 2:
                plain = plain[1:-1]
            plain = plain.replace('\\', '\\').replace('\n', ' ').replace('\t', ' ')
            ax.text(0.01, 0.5, plain, fontsize=size, color=color, va='center', ha='left')
            fig.savefig(
                out_path,
                format='png',
                dpi=180,
                bbox_inches='tight',
                pad_inches=0.02,
                facecolor='white',
            )
    return out_path.as_uri() if os.name != 'nt' else out_path.resolve().as_uri()


def markdown_math_to_html(markdown: str, *, text_color: str = '#111827') -> str:
    """Render a small Markdown subset and MathText formulas for QTextBrowser.

    Qt rich text supports HTML images, but not MathJax. We therefore render
    TeX-like expressions with Matplotlib MathText into cached PNG files and
    embed them as <img> tags.
    """

    blocks = _split_display_math(markdown)
    html_parts = [
        '<html><body style="font-family: Segoe UI, Arial, sans-serif; '
        f'color: {text_color}; line-height: 1.42; margin: 12px;">'
    ]
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            html_parts.append('</ul>')
            in_list = False

    for kind, value in blocks:
        if kind == 'math':
            close_list()
            uri = render_math_to_path(f'${value.strip()}$', size=17, color='black')
            html_parts.append(
                '<div style="text-align:center; margin:10px 0 12px 0;">'
                f'<img src="{html.escape(uri)}" />'
                '</div>'
            )
            continue

        for raw_line in value.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                close_list()
                html_parts.append('<div style="height:6px;"></div>')
                continue
            if stripped.startswith('#'):
                close_list()
                level = min(3, len(stripped) - len(stripped.lstrip('#')))
                title = stripped[level:].strip()
                sizes = {1: 22, 2: 18, 3: 15}
                html_parts.append(
                    f'<h{level} style="font-size:{sizes[level]}px; margin:12px 0 6px 0;">'
                    f'{_inline_math(title)}</h{level}>'
                )
                continue
            if stripped.startswith(('- ', '* ')):
                if not in_list:
                    html_parts.append('<ul style="margin-top:4px;">')
                    in_list = True
                html_parts.append(f'<li>{_inline_math(stripped[2:].strip())}</li>')
                continue
            if re.match(r'^\d+\.\s+', stripped):
                close_list()
                html_parts.append(f'<p>{_inline_math(re.sub(r"^\d+\.\s+", "", stripped))}</p>')
                continue
            close_list()
            html_parts.append(f'<p>{_inline_math(stripped)}</p>')

    close_list()
    html_parts.append('</body></html>')
    return ''.join(html_parts)


def _split_display_math(markdown: str):
    parts = []
    pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    pos = 0
    for match in pattern.finditer(markdown):
        if match.start() > pos:
            parts.append(('text', markdown[pos:match.start()]))
        parts.append(('math', match.group(1)))
        pos = match.end()
    if pos < len(markdown):
        parts.append(('text', markdown[pos:]))
    return parts


def _inline_math(text: str) -> str:
    protected = []

    def protect_code(match):
        protected.append(f'<code>{html.escape(match.group(1))}</code>')
        return f'\x00{len(protected) - 1}\x00'

    text = re.sub(r'`([^`]+)`', protect_code, text)
    escaped = html.escape(text)
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped)

    def replace_math(match):
        expr = match.group(1).strip()
        if not expr:
            return ''
        uri = render_math_to_path(f'${expr}$', size=14, color='black')
        return f'<img src="{html.escape(uri)}" style="vertical-align:middle;" />'

    escaped = re.sub(r'(?<!\\)\$([^$\n]+?)(?<!\\)\$', replace_math, escaped)
    escaped = escaped.replace(r'\$', '$')
    for idx, value in enumerate(protected):
        escaped = escaped.replace(f'\x00{idx}\x00', value)
    return escaped
