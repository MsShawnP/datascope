"""Brand font registration for ReportLab PDFs.

Registers the Lailara Design System typefaces — Playfair Display (serif,
weights 400/700) and Source Sans 3 (sans, weights 400/600) — with ReportLab
so generated PDFs embed the real brand fonts instead of falling back to the
base-14 Helvetica/Times faces.

Usage::

    from lailara_palette.fonts import register_fonts, SERIF, SERIF_BOLD, SANS, SANS_BOLD

    register_fonts()  # idempotent — safe to call once at import or per render
    ParagraphStyle("body", fontName=SANS)
    ParagraphStyle("heading", fontName=SERIF_BOLD)

After ``register_fonts()``, ReportLab also resolves ``<b>`` markup: a
Paragraph whose ``fontName`` is ``SERIF``/``SANS`` renders bold runs with the
matching 700/600 face via the registered font families.

The fonts are SIL Open Font License 1.1 (see the ``OFL-*.txt`` files bundled
in this package). ``reportlab`` is an optional dependency; install it with
``pip install lailara-palette[pdf]``.
"""
from importlib import resources

# Registered ReportLab font names. Import these rather than hardcoding strings.
SERIF = "Playfair Display"
SERIF_BOLD = "Playfair Display Bold"
SANS = "Source Sans 3"
SANS_BOLD = "Source Sans 3 SemiBold"

# Registered name -> bundled TTF filename.
_FONT_FILES = {
    SERIF: "PlayfairDisplay-Regular.ttf",
    SERIF_BOLD: "PlayfairDisplay-Bold.ttf",
    SANS: "SourceSans3-Regular.ttf",
    SANS_BOLD: "SourceSans3-SemiBold.ttf",
}

_registered = False


def register_fonts() -> None:
    """Register the brand TTFs with ReportLab's global font registry.

    Idempotent: the first call registers all four faces plus the two font
    families (so ``<b>`` markup maps 400 -> bold); later calls are no-ops.
    Raises ``ImportError`` if ReportLab is not installed.
    """
    global _registered
    if _registered:
        return

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_dir = resources.files(__name__)
    for name, filename in _FONT_FILES.items():
        # as_file yields a real filesystem path (a temp copy only when the
        # package lives inside a zip). TTFont parses the file eagerly, so the
        # read happens while the path is still valid.
        with resources.as_file(font_dir / filename) as path:
            pdfmetrics.registerFont(TTFont(name, str(path)))

    pdfmetrics.registerFontFamily(
        SERIF, normal=SERIF, bold=SERIF_BOLD, italic=SERIF, boldItalic=SERIF_BOLD
    )
    pdfmetrics.registerFontFamily(
        SANS, normal=SANS, bold=SANS_BOLD, italic=SANS, boldItalic=SANS_BOLD
    )

    # ReportLab seeds every canvas's initial font from this config value
    # (default: Helvetica), which registers Helvetica in each page's font
    # resources even when no glyphs are drawn with it — enough to make
    # `pdffonts` report a non-embedded Helvetica. Point the base at the brand
    # sans so generated PDFs reference only the embedded brand faces.
    from reportlab import rl_config

    rl_config.canvas_basefontname = SANS
    _registered = True


__all__ = ["register_fonts", "SERIF", "SERIF_BOLD", "SANS", "SANS_BOLD"]
