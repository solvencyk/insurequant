"""A11y color-check utilities: WCAG contrast ratio + colorblind confusability.

Companion to docs/a11y_baseline.md. Two things this repo needs checked whenever
a color token or chart palette changes, done with math instead of eyeballing:

1. WCAG 2.1 contrast ratio between a text/foreground color and its background
   (standard relative-luminance formula). AA thresholds: 4.5:1 normal text,
   3:1 large text (>=24px, or >=19px bold) / UI component boundaries.

2. Colorblind confusability: simulates protanopia/deuteranopia (Brettel/Viénot-
   style linear-RGB matrix approximation) and reports the Euclidean RGB
   distance between two colors under simulation. Rule of thumb used in the
   2026-07-21 audit: delta < ~60 (out of a max ~441) is worth a second look
   when the two colors are used together to distinguish chart series.

Usage:
    python scripts/a11y_contrast_check.py contrast "#6c757d" "#f8f9fa"
    python scripts/a11y_contrast_check.py cbcheck "#dc3545" "#fd7e14"

Or import and call contrast_ratio() / simulate() / cb_distance() directly.
"""

import sys

import numpy as np

_PROTANOPIA = np.array([
    [0.567, 0.433, 0.0],
    [0.558, 0.442, 0.0],
    [0.0,   0.242, 0.758],
])
_DEUTERANOPIA = np.array([
    [0.625, 0.375, 0.0],
    [0.7,   0.3,   0.0],
    [0.0,   0.3,   0.7],
])


def hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _srgb_to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    out = np.where(c <= 0.0031308, c * 12.92, 1.055 * (c ** (1 / 2.4)) - 0.055)
    return np.clip(out * 255, 0, 255)


def relative_luminance(rgb):
    lin = _srgb_to_linear(np.array(rgb, dtype=float))
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast_ratio(rgb1, rgb2):
    """WCAG contrast ratio, 1:1 (identical) to 21:1 (black/white)."""
    l1, l2 = relative_luminance(rgb1), relative_luminance(rgb2)
    l1, l2 = max(l1, l2), min(l1, l2)
    return (l1 + 0.05) / (l2 + 0.05)


def simulate(rgb, kind):
    """kind: 'protanopia' or 'deuteranopia'."""
    matrix = _PROTANOPIA if kind == "protanopia" else _DEUTERANOPIA
    lin = _srgb_to_linear(np.array(rgb, dtype=float))
    return _linear_to_srgb(matrix @ lin)


def cb_distance(rgb1, rgb2, kind):
    """Euclidean RGB distance between two colors after colorblind simulation."""
    s1, s2 = simulate(rgb1, kind), simulate(rgb2, kind)
    return float(np.linalg.norm(s1 - s2))


def _main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    mode, a, b = sys.argv[1], hex_to_rgb(sys.argv[2]), hex_to_rgb(sys.argv[3])
    if mode == "contrast":
        c = contrast_ratio(a, b)
        verdict = "OK (AA normal text)" if c >= 4.5 else (
            "OK (AA large text/UI only)" if c >= 3.0 else "FAIL"
        )
        print(f"contrast = {c:.2f}:1  ->  {verdict}")
    elif mode == "cbcheck":
        for kind in ("protanopia", "deuteranopia"):
            d = cb_distance(a, b, kind)
            flag = " <-- close, may be confused" if d < 60 else ""
            print(f"{kind:12s} delta-RGB = {d:6.1f}{flag}")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    _main()
