"""Actores: sprites PNG (estáticos) y personajes procedurales animados (zombi)."""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


class Sprite:
    """PNG RGBA con colores base (sin luz). Un .json al lado puede definir el 'ancla' (pies)."""

    def __init__(self, path):
        path = Path(path)
        im = Image.open(path).convert("RGBA")
        self.img = im
        meta = path.with_suffix(".json")
        info = json.loads(meta.read_text()) if meta.exists() else {}
        self.ancla = tuple(info.get("ancla", (im.width // 2, im.height - 1)))

    def place(self, alb, alpha, x, y, escala=1.0, espejo=False):
        """Pega el sprite con sus pies en (x, y). Devuelve la máscara colocada."""
        im = self.img
        ax, ay = self.ancla
        if espejo:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            ax = im.width - 1 - ax
        if escala != 1.0:
            im = im.resize((max(1, round(im.width * escala)), max(1, round(im.height * escala))), Image.NEAREST)
            ax, ay = ax * escala, ay * escala
        arr = np.asarray(im, np.float32)
        m = arr[..., 3] > 127
        x0, y0 = int(round(x - ax)), int(round(y - ay))
        H, W = alpha.shape
        sx0, sy0 = max(0, -x0), max(0, -y0)
        dx0, dy0 = max(0, x0), max(0, y0)
        w = min(arr.shape[1] - sx0, W - dx0)
        h = min(arr.shape[0] - sy0, H - dy0)
        placed = np.zeros_like(alpha)
        if w <= 0 or h <= 0:
            return placed
        mm = m[sy0:sy0 + h, sx0:sx0 + w]
        region = alb[dy0:dy0 + h, dx0:dx0 + w]
        region[mm] = arr[sy0:sy0 + h, sx0:sx0 + w, :3][mm]
        alpha[dy0:dy0 + h, dx0:dx0 + w] |= mm
        placed[dy0:dy0 + h, dx0:dx0 + w] = mm
        return placed


def rim_light(placed, em, lights):
    """Borde iluminado del lado de las luces marcadas con contraluz=True."""
    ys, xs = np.nonzero(placed)
    if len(xs) == 0:
        return
    cx, cy = xs.mean(), ys.mean()
    for L in lights:
        if not L.contraluz:
            continue
        ly, lx = np.unravel_index(np.argmax(L.mapa), L.mapa.shape)
        k = float(L.mapa[int(cy), int(cx)])
        if k < 0.08:
            continue
        shift = 2 if lx < cx else -2
        edge = placed & ~np.roll(placed, shift, axis=1)
        edge[int(ys.max()) - 6:, :] = False         # no iluminar los pies
        em[edge] += np.array(L.color, np.float32) * 160 * min(k, 1.0)


# ------------------------------------------------------- zombi procedural ---
ROPA = [(74, 40, 20), (58, 72, 60), (102, 40, 34), (60, 66, 70), (84, 60, 40), (50, 50, 50)]


def draw_zombie(img, alpha, z, t, i=0):
    """z: {pos: [x, y], altura, fase, ropa, avanza: [dx, dy] por segundo}"""
    x, y = z["pos"]
    h = z.get("altura", 20)
    ph = z.get("fase", i * 1.3)
    cloth = tuple(z.get("ropa", ROPA[i % len(ROPA)]))
    if z.get("avanza"):
        dx, dy = z["avanza"]
        x, y = x + dx * t, y + dy * t
        h = h * (1 + dy * t / max(y, 1) * 0.9)
    d, dm = ImageDraw.Draw(img), ImageDraw.Draw(alpha)
    sway = math.sin(t * 2.2 + ph) * h * 0.06
    step = (int((t + ph) / 0.45) % 2) * 2 - 1
    skin = (120, 128, 98)
    hx, hy = x + sway * 1.5, y - h * 0.88
    for g, cs, cc, cd in ((d, skin, cloth, (30, 30, 28)), (dm, 255, 255, 255)):
        lw = max(1, int(h * 0.09))
        g.line([(x - h * .06, y - h * .45), (x - h * .08 + step * h * .05, y)], fill=cd, width=lw)
        g.line([(x + h * .06, y - h * .45), (x + h * .08 - step * h * .05, y)], fill=cd, width=lw)
        g.polygon([(x - h * .13 + sway, y - h * .8), (x + h * .12 + sway, y - h * .78), (x + h * .09, y - h * .44),
                   (x - h * .1, y - h * .44)], fill=cc)
        aw = max(1, int(h * 0.07))
        g.line([(x + h * .1 + sway, y - h * .76), (x + h * .3 + sway, y - h * .62)], fill=cs, width=aw)
        g.line([(x - h * .12 + sway, y - h * .76), (x - h * .16 + sway * .5, y - h * .48)], fill=cs, width=aw)
        r = max(1.0, h * 0.09)
        g.ellipse([hx - r, hy - r, hx + r, hy + r], fill=cs)
