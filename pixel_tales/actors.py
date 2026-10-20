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
        self.brillos = info.get("brillos", [])   # [{pos: [x, y], color: [r, g, b]}] puntos que brillan solos

    def place(self, alb, alpha, x, y, escala=1.0, espejo=False, em=None):
        """Pega el sprite con sus pies en (x, y). Devuelve la máscara colocada."""
        im = self.img
        ax, ay = self.ancla
        glow = [(b["pos"][0], b["pos"][1], b.get("color", [255, 60, 40])) for b in self.brillos]
        if espejo:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            ax = im.width - 1 - ax
            glow = [(im.width - 1 - gx, gy, c) for gx, gy, c in glow]
        if escala != 1.0:
            im = im.resize((max(1, round(im.width * escala)), max(1, round(im.height * escala))), Image.NEAREST)
            ax, ay = ax * escala, ay * escala
            glow = [(gx * escala, gy * escala, c) for gx, gy, c in glow]
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
        if em is not None:
            for gx, gy, c in glow:
                px, py = int(round(x0 + gx)), int(round(y0 + gy))
                if 0 <= px < W and 0 <= py < H:
                    em[py, px] = c
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


# ---------------------------------------------------------- murciélagos ---
def draw_bats(img, alpha, cfg, t, i=0):
    """cfg: {cantidad, zona: [x0, y0, x1, y1], tam}. Vuelan en círculos aleatorios dentro de la zona."""
    rng = np.random.default_rng(cfg.get("semilla", 5) + i)
    x0, y0, x1, y1 = cfg.get("zona", [0, 0, img.width, img.height // 2])
    d, dm = ImageDraw.Draw(img), ImageDraw.Draw(alpha)
    col = tuple(cfg.get("color", (10, 8, 10)))
    for k in range(cfg.get("cantidad", 10)):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        rx, ry = rng.uniform(8, 40), rng.uniform(4, 18)
        sp, ph = rng.uniform(0.6, 1.6) * rng.choice([-1, 1]), rng.uniform(0, 6.3)
        s = cfg.get("tam", 1.0) * rng.uniform(0.7, 1.3)
        x = cx + rx * math.cos(t * sp + ph)
        y = cy + ry * math.sin(t * sp * 1.3 + ph)
        flap = math.sin(t * 18 + ph * 3)
        wy = -3 * s * flap
        pts = [(x - 5 * s, y + wy), (x - 2 * s, y - 1 * s), (x, y + 1 * s), (x + 2 * s, y - 1 * s), (x + 5 * s, y + wy),
               (x + 2 * s, y + 1.5 * s), (x, y + 2 * s), (x - 2 * s, y + 1.5 * s)]
        for g, c in ((d, col), (dm, 255)):
            g.polygon(pts, fill=c)


# ------------------------------------------------------------ escorpiones ---
def draw_scorpions(img, alpha, cfg, t, i=0):
    """cfg: {cantidad, zona: [x0, y0, x1, y1], tam}. Caminan lento de un lado a otro."""
    rng = np.random.default_rng(cfg.get("semilla", 11) + i)
    x0, y0, x1, y1 = cfg["zona"]
    d, dm = ImageDraw.Draw(img), ImageDraw.Draw(alpha)
    col = tuple(cfg.get("color", (40, 26, 20)))
    for k in range(cfg.get("cantidad", 8)):
        bx, by = rng.uniform(x0, x1), rng.uniform(y0, y1)
        dirx = rng.choice([-1, 1])
        sp = rng.uniform(1.5, 4)
        s = cfg.get("tam", 1.0) * (0.6 + 0.8 * (by - y0) / max(y1 - y0, 1))
        x = x0 + (bx - x0 + dirx * sp * t) % max(x1 - x0, 1)
        y = by
        leg = int(t * 8 + k) % 2
        for g, c in ((d, col), (dm, 255)):
            g.ellipse([x - 3 * s, y - 1.2 * s, x + 3 * s, y + 1.2 * s], fill=c)
            g.line([(x - 3 * s * dirx, y), (x - 5 * s * dirx, y - 2 * s), (x - 4 * s * dirx, y - 4 * s),
                    (x - 2.5 * s * dirx, y - 3.5 * s)], fill=c, width=max(1, int(s)))
            g.line([(x + 3 * s * dirx, y), (x + 5 * s * dirx, y - 1 * s)], fill=c, width=max(1, int(s)))
            for j in (-1.5, 0, 1.5):
                g.line([(x + j * s, y), (x + j * s - s, y + (1.5 + leg) * s)], fill=c, width=1)


# ------------------------------------------------------------------- ojos ---
def draw_eyes(rgb, alpha, cfg, t, i=0):
    """Ojos brillando en la oscuridad (se dibujan ya con color final, no les afecta la luz).
    cfg: {pos: [x, y], color: [r, g, b], separacion, tam, aparece: segundo}"""
    if t < cfg.get("aparece", 0):
        return
    x, y = cfg["pos"]
    sep = cfg.get("separacion", 4)
    tam = cfg.get("tam", 1)
    ph = cfg.get("fase", i * 1.7)
    if ((t * 0.9 + ph) % 3.3) < 0.12:          # parpadeo
        return
    c = np.array(cfg.get("color", [255, 70, 40]), np.uint8)
    dim = (c.astype(np.float32) * 0.45).astype(np.uint8)
    H, W = alpha.shape
    for ex in (x - sep / 2, x + sep / 2):
        for dx in range(-tam, tam + 1):
            for dy in range(-((tam + 1) // 2), (tam + 1) // 2 + 1):
                px, py = int(ex + dx), int(y + dy)
                if 0 <= px < W and 0 <= py < H:
                    edge = abs(dx) == tam
                    rgb[py, px] = dim if edge else c
                    alpha[py, px] = True


# ------------------------------------------------------ sprites animados ---
class MovingSprite:
    """Sprite que aparece en un momento y/o se desplaza: {sprite, pos, escala, espejo, aparece, movimiento: [dx, dy]}.
    `flota: px` lo hace subir y bajar suave (lanchas, respiración)."""

    def __init__(self, path, cfg):
        im = Image.open(path).convert("RGBA")
        meta = Path(path).with_suffix(".json")
        info = json.loads(meta.read_text()) if meta.exists() else {}
        ax, ay = info.get("ancla", (im.width // 2, im.height - 1))
        if cfg.get("espejo"):
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            ax = im.width - 1 - ax
        e = cfg.get("escala", 1.0)
        if e != 1.0:
            im = im.resize((max(1, round(im.width * e)), max(1, round(im.height * e))), Image.NEAREST)
            ax, ay = ax * e, ay * e
        self.im, self.ax, self.ay, self.cfg = im, ax, ay, cfg
        a = np.asarray(im)[..., 3] > 127
        self.mask = Image.fromarray((a * 255).astype(np.uint8))

    def __call__(self, img, alpha, cfg, t, i=0):
        c = self.cfg
        if t < c.get("aparece", 0) or t > c.get("desaparece", 1e9):
            return
        x, y = c["pos"]
        dx, dy = c.get("movimiento", (0, 0))
        tt = t - c.get("aparece", 0)
        x, y = x + dx * tt, y + dy * tt + c.get("flota", 0) * math.sin(t * 1.6 + i)
        px, py = int(round(x - self.ax)), int(round(y - self.ay))
        img.paste(self.im.convert("RGB"), (px, py), self.mask)
        alpha.paste(255, (px, py, px + self.im.width, py + self.im.height), self.mask)
