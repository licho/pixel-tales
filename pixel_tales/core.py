"""Piezas básicas: tamaños, paleta con tramado, ruido, máscaras, luces."""
import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw

# Cada capa se pinta a LW x LH "pixeles de arte". La cámara ve VW x VH.
# El margen (LW - VW) es para el parallax. Se escala x S al exportar.
LW, LH = 424, 216
VW, VH = 384, 216
S = 5

# formato -> (ancho capa, alto capa, ancho vista, alto vista). Salida = vista x S.
FORMATOS = {
    "horizontal": (424, 216, 384, 216),   # 1920x1080
    "vertical": (256, 384, 216, 384),     # 1080x1920 (reels)
}

_BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16 - 0.5
_GRIDS, _BAYER_TILES = {}, {}


def grid(w=LW, h=LH):
    """Coordenadas XX, YY (float) de una capa. Se cachean."""
    if (w, h) not in _GRIDS:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _GRIDS[(w, h)] = (xx, yy)
    return _GRIDS[(w, h)]


class Palette:
    """Paleta fija + tramado Bayer. Usa una tabla precalculada (rápida)."""

    def __init__(self, colors, spread=13.0):
        self.colors = np.array(colors, np.float32)
        self.colors_u8 = self.colors.astype(np.uint8)
        self.spread = float(spread)
        g = np.arange(64, dtype=np.float32) * 4 + 2
        r, gg, b = np.meshgrid(g, g, g, indexing="ij")
        pts = np.stack([r, gg, b], -1).reshape(-1, 3)
        idx = np.empty(len(pts), np.uint8)
        for i in range(0, len(pts), 16384):
            c = pts[i:i + 16384, None, :]
            idx[i:i + 16384] = ((c - self.colors[None]) ** 2).sum(-1).argmin(1)
        self.lut = idx.reshape(64, 64, 64)

    def quantize(self, rgb):
        h, w, _ = rgb.shape
        if (h, w) not in _BAYER_TILES:
            _BAYER_TILES[(h, w)] = np.tile(_BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
        c = np.clip(rgb + _BAYER_TILES[(h, w)] * self.spread, 0, 255).astype(np.int32) >> 2
        return self.colors_u8[self.lut[c[..., 0], c[..., 1], c[..., 2]]]


# ------------------------------------------------------------------ ruido ---
def vnoise(w, h, cell, seed):
    rng = np.random.default_rng(seed)
    gw, gh = w // cell + 3, h // cell + 3
    im = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8))
    im = im.resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(im, np.float32)[:h, :w] / 255


def fbm(w, h, seed, cells=(48, 24, 12, 6)):
    out, amp, tot = 0, 1.0, 0
    for i, c in enumerate(cells):
        out = out + vnoise(w, h, c, seed + i) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def mask(fn, w=LW, h=LH):
    """Máscara booleana dibujando con PIL: mask(lambda d: d.polygon(...))."""
    m = Image.new("L", (w, h), 0)
    fn(ImageDraw.Draw(m))
    return np.asarray(m) > 127


def upscale(a, s=S):
    return np.repeat(np.repeat(a, s, 0), s, 1)


# ------------------------------------------------------------------ luces ---
@dataclass
class Light:
    """Luz de la escena. `mapa` es la intensidad por pixel; `parpadeo`: None | 'fuego' | 'farol'."""
    nombre: str
    mapa: np.ndarray
    color: tuple
    parpadeo: str = None
    contraluz: bool = False        # pinta un borde de luz en los actores cercanos
    volumen: np.ndarray = None     # haz de luz/niebla iluminada (RGB aditivo), opcional
    rgb: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        self.rgb = self.mapa[..., None] * np.array(self.color, np.float32)


def point_light(x, y, radio, intensidad, w=LW, h=LH):
    xx, yy = grid(w, h)
    return intensidad * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * radio ** 2))


def pool_light(x, y, rx, ry, intensidad, y_min=0, w=LW, h=LH):
    """Charco de luz elíptico sobre el piso."""
    xx, yy = grid(w, h)
    return intensidad * np.exp(-((xx - x) / rx) ** 2 - ((yy - y) / ry) ** 2) * (yy > y_min)


def flicker(tipo, t, semilla=0.0):
    """Multiplicador de intensidad de una luz en el tiempo t (segundos del panel)."""
    if tipo == "fuego":
        return 0.9 + 0.12 * math.sin(t * 23 + semilla) + 0.08 * math.sin(t * 37 + 1 + semilla)
    if tipo == "farol":
        ph = (t + semilla) % 4.3
        return 0.15 if (3.1 < ph < 3.2 or 3.28 < ph < 3.33) else 1.0
    return 1.0
