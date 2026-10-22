"""Pinceles reutilizables para escenas: roca, antorchas, calaveras, estrellas, estalactitas."""
import math

import numpy as np

from .core import Light, fbm, smooth, vnoise

FUEGO = (1.0, 0.55, 0.22)


def roca(scene, base=(58, 46, 44), seed=0, contraste=0.6, grietas=True):
    """Textura de roca (H, W, 3) para usar como albedo."""
    W, H = scene.W, scene.H
    n = fbm(W, H, 100 + seed, (32, 16, 8, 4))
    relieve = np.clip(1 + 9 * (n - np.roll(np.roll(n, 2, 0), 2, 1)), 0.55, 1.5)   # luz desde arriba-izq
    col = np.array(base, np.float32) * ((1 - contraste / 2 + contraste * n) * relieve)[..., None]
    if grietas:
        c = fbm(W, H, 200 + seed, (24, 12, 6))
        col[(np.abs(c - 0.5) < 0.005) & (n > 0.45)] *= 0.55
    col += ((vnoise(W, H, 2, 300 + seed) - 0.5) * 10)[..., None]
    return col


def piedra_bloques(scene, base=(70, 62, 56), bw=14, bh=7, seed=0):
    """Muro de bloques de piedra (H, W, 3)."""
    W, H = scene.W, scene.H
    xx, yy = scene.grid()
    row = np.floor(yy / bh)
    xs = xx + (row % 2) * bw / 2
    col = roca(scene, base, seed, 0.35, grietas=False)
    joint = ((yy % bh) < 1) | ((xs % bw) < 1)
    col[joint] *= 0.55
    return col


def antorcha(scene, x, y, tam=1.0, radio=None, intensidad=1.1, contraluz=True):
    """Antorcha en pared: soporte + flama animada + luz que parpadea."""
    alb, a = scene.mid_alb, scene.mid_a
    s = tam
    m = scene.mask(lambda d: (d.line([(x, y), (x, y + 10 * s)], fill=255, width=max(1, int(2 * s))),
                              d.polygon([(x - 3 * s, y - 1), (x + 3 * s, y - 1), (x + 2 * s, y + 3 * s),
                                         (x - 2 * s, y + 3 * s)], fill=255)))
    alb[m] = (40, 28, 22)
    a |= m
    scene.fires.append({"x0": int(x - 3 * s), "x1": int(x + 3 * s) + 1, "y": int(y - 1), "tam": 0.55 * s,
                        "humo": False})
    scene.lights.append(Light(f"antorcha{len(scene.lights)}", scene.point(x, y - 4 * s, (radio or 34) * s,
                                                                          intensidad), FUEGO,
                              parpadeo="fuego", contraluz=contraluz))


def brasero(scene, x, y, tam=1.0, intensidad=1.2):
    """Brasero de piedra en el piso (x, y = base) con fuego y humo de copal."""
    s = tam
    m = scene.mask(lambda d: (d.polygon([(x - 9 * s, y - 10 * s), (x + 9 * s, y - 10 * s), (x + 6 * s, y - 4 * s),
                                         (x - 6 * s, y - 4 * s)], fill=255),
                              d.rectangle([x - 3 * s, y - 4 * s, x + 3 * s, y], fill=255),
                              d.rectangle([x - 6 * s, y - 1, x + 6 * s, y], fill=255)))
    scene.mid_alb[m] = (82, 70, 60)
    scene.mid_alb[m & (scene.grid()[1] < y - 9 * s)] = (110, 98, 84)
    scene.mid_a |= m
    scene.fires.append({"x0": int(x - 7 * s), "x1": int(x + 7 * s) + 1, "y": int(y - 10 * s), "tam": 1.0 * s,
                        "humo": True})
    scene.lights.append(Light(f"brasero{len(scene.lights)}", scene.point(x, y - 14 * s, 46 * s, intensidad), FUEGO,
                              parpadeo="fuego", contraluz=True))


def calavera(d, x, y, s=1.0, hueso=(196, 184, 152), hueco=(16, 12, 14)):
    """Dibuja una calavera pequeña con ImageDraw sobre una imagen RGB (x, y = centro)."""
    d.ellipse([x - 3 * s, y - 3 * s, x + 3 * s, y + 2 * s], fill=hueso)
    d.rectangle([x - 2 * s, y + 1 * s, x + 2 * s, y + 3.5 * s], fill=hueso)
    if s >= 1:
        d.rectangle([x - 2 * s, y - 1 * s, x - 1 * s, y], fill=hueco)
        d.rectangle([x + 1 * s, y - 1 * s, x + 2 * s, y], fill=hueco)
        d.point([(x, y + 1 * s)], fill=hueco)


def estrellas(scene, col, densidad=0.004, y_max=0.5, seed=0, color=(196, 184, 152)):
    rng = np.random.default_rng(seed)
    n = int(scene.W * scene.H * y_max * densidad)
    for _ in range(n):
        x, y = rng.integers(0, scene.W), rng.integers(0, int(scene.H * y_max))
        k = rng.uniform(0.35, 1.0)
        col[y, x] = np.array(color, np.float32) * k


def estalactitas(scene, d, y_base, x0, x1, largo=30, seed=0, fill=255):
    """Picos colgando desde y_base (en una máscara de ImageDraw)."""
    rng = np.random.default_rng(seed)
    x = x0
    while x < x1:
        w = rng.uniform(4, 14)
        L = rng.uniform(0.3, 1.0) * largo
        d.polygon([(x, y_base), (x + w, y_base), (x + w * rng.uniform(0.3, 0.7), y_base + L)], fill=fill)
        x += w * rng.uniform(0.6, 1.2)


def niebla_profundidad(scene, col, cx, cy, radio, minimo=0.0):
    """Oscurece hacia un punto (fondo de un túnel): multiplica el color."""
    xx, yy = scene.grid()
    d = np.hypot((xx - cx) / scene.W, (yy - cy) / scene.H)
    k = minimo + (1 - minimo) * smooth(0.0, radio, d)
    col *= k[..., None]
    return col


def fogata(scene, x, y, w, radio=3.2, intensidad=0.95):
    """Fogata en el suelo (x, y = base, w = ancho): leños cruzados, piedras, flamas, humo y luz que parpadea."""
    m = scene.mask(lambda d: (d.line([(x - w / 2, y), (x + w / 2, y - w * 0.15)], fill=255, width=max(1, int(w / 6))),
                              d.line([(x - w / 2, y - w * 0.15), (x + w / 2, y)], fill=255, width=max(1, int(w / 6)))))
    scene.mid_alb[m] = (70, 44, 26)
    scene.mid_a |= m
    for i in range(7):
        a = math.pi * i / 6
        sx, sy = x + math.cos(a) * w * 0.65, y + 1 + math.sin(a) * w * 0.12
        st = scene.mask(lambda d: d.ellipse([sx - w * 0.08, sy - w * 0.06, sx + w * 0.08, sy + w * 0.06], fill=255))
        scene.mid_alb[st] = (90, 86, 80)
        scene.mid_a |= st
    scene.fires.append({"x0": int(x - w * 0.35), "x1": int(x + w * 0.35) + 1, "y": int(y - w * 0.12),
                        "tam": w / 12, "humo": True})
    scene.lights.append(Light(f"fogata{len(scene.lights)}", scene.point(x, y - w * 0.3, w * radio, intensidad), FUEGO,
                              parpadeo="fuego", contraluz=True))
