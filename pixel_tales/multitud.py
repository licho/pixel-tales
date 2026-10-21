"""Ejércitos en perspectiva (miles de soldados marchando) y estandartes que ondean.

Se usan como actores en el episodio:
  - ejercito: {zona: [x0, y0, x1, y1], tipo: persa|qin|romano|indio, alto_cerca: 40, alto_lejos: 3,
               avance: -6, marcha: true, bloques: [12, 3], estandartes: 14, densidad: 1.0, bruma: [r,g,b],
               poligono: [[x, y], ...]}
    y0 = base de la fila más lejana, y1 = base de la fila más cercana (px de la capa).
  - estandarte: {pos: [x, y], alto: 60, ancho: 26, color: [r,g,b], color2: [r,g,b],
                 simbolo: aguila|sol|rueda|dragon|nada, fase: 0}
"""
import math

import numpy as np
from PIL import Image, ImageDraw

TIPOS = {
    #        túnica(s)                                        escudo            casco           lanza
    "persa": ([(150, 110, 60), (70, 60, 120), (164, 38, 30), (190, 148, 64)], (176, 136, 86), (60, 50, 70), (150, 120, 80)),
    "qin":   ([(30, 26, 30), (44, 36, 40), (38, 30, 32)], (60, 40, 30), (40, 34, 36), (150, 110, 50)),
    "romano": ([(164, 38, 30), (150, 34, 28)], (180, 44, 32), (150, 150, 156), (130, 100, 60)),
    "mexica": ([(220, 210, 180), (196, 150, 70), (170, 60, 40), (60, 110, 80)], (60, 90, 150), (200, 170, 110), (110, 80, 50)),
    "indio": ([(220, 200, 160), (200, 150, 70), (180, 120, 60)], (140, 100, 50), (200, 170, 110), (140, 110, 70)),
}
PIEL = (150, 104, 70)


def _soldado(d, x, yb, h, tipo, rng, banderas=None):
    tun, escudo, casco, lanza = TIPOS.get(tipo, TIPOS["persa"])
    t = tun[int(rng.integers(0, len(tun)))]
    if h < 2.2:                                   # muy lejos: puntos y lanzas
        d.point((x, yb - 1), fill=t)
        d.line([(x + 0.6, yb - 2.6 * max(h, 1)), (x + 0.6, yb - 1)], fill=lanza)
        return
    if h < 6:                                     # lejos: silueta mínima
        d.line([(x, yb - h * 0.8), (x, yb)], fill=t)
        d.point((x, yb - h * 0.95), fill=casco)
        d.line([(x + 1, yb - h * 1.4), (x + 1, yb - h * 0.3)], fill=lanza)
        return
    w = h * 0.16
    d.rectangle([x - w * 0.8, yb - h * 0.3, x - w * 0.15, yb], fill=(50, 38, 30))           # piernas
    d.rectangle([x + w * 0.15, yb - h * 0.3, x + w * 0.8, yb], fill=(44, 34, 28))
    d.rectangle([x - w, yb - h * 0.76, x + w, yb - h * 0.28], fill=t)                         # torso
    d.ellipse([x - w * 0.75, yb - h * 0.98, x + w * 0.75, yb - h * 0.76], fill=PIEL)         # cabeza
    d.pieslice([x - w * 0.85, yb - h * 1.02, x + w * 0.85, yb - h * 0.8], 180, 360, fill=casco)
    if tipo == "romano":
        d.line([(x, yb - h * 1.06), (x, yb - h * 0.98)], fill=(164, 38, 30), width=max(1, int(h * 0.05)))
    lx = x + w * 1.4
    d.line([(lx, yb - h * 1.45), (lx, yb - h * 0.2)], fill=lanza, width=max(1, int(h * 0.04)))   # lanza
    d.polygon([(lx - h * 0.03, yb - h * 1.45), (lx + h * 0.03, yb - h * 1.45), (lx, yb - h * 1.55)], fill=(190, 180, 160))
    if tipo == "romano":                                                                       # escudo rectangular
        d.rectangle([x - w * 1.6, yb - h * 0.72, x - w * 0.1, yb - h * 0.22], fill=escudo)
        d.point((x - w * 0.85, yb - h * 0.47), fill=(190, 148, 64))
    else:
        d.ellipse([x - w * 1.7, yb - h * 0.72, x - w * 0.1, yb - h * 0.3], fill=escudo)
    if banderas is not None:                                                                    # estandarte de fila
        c1, c2 = banderas
        d.line([(lx, yb - h * 2.1), (lx, yb - h * 0.2)], fill=(90, 66, 34), width=max(1, int(h * 0.05)))
        d.rectangle([lx, yb - h * 2.05, lx + h * 0.5, yb - h * 1.7], fill=c1)
        d.line([(lx, yb - h * 1.72), (lx + h * 0.5, yb - h * 1.72)], fill=c2)


BANDERAS = {"persa": ((70, 60, 120), (190, 148, 64)), "qin": ((26, 22, 24), (164, 38, 30)),
            "romano": ((164, 38, 30), (190, 148, 64)), "indio": ((236, 140, 62), (232, 224, 200)), "mexica": ((60, 110, 80), (236, 200, 70))}


class Ejercito:
    def __init__(self, cfg, W, H):
        self.cfg, self.W, self.H = cfg, W, H
        x0, y0, x1, y1 = cfg["zona"]
        self.x0, self.zw = int(x0), int(x1 - x0)
        tipo = cfg.get("tipo", "persa")
        hl, hc = float(cfg.get("alto_lejos", 3)), float(cfg.get("alto_cerca", 40))
        dens = float(cfg.get("densidad", 1.0))
        bruma = np.array(cfg.get("bruma", [200, 150, 110]), np.float32)
        bloques = cfg.get("bloques")
        cada = int(cfg.get("estandartes", 0))
        rng = np.random.default_rng(int(cfg.get("semilla", 4)))
        self.avance = float(cfg.get("avance", -6))
        self.marcha = bool(cfg.get("marcha", self.avance != 0))
        self.y = y1
        self.filas = []
        y = float(y0)
        j = 0
        while y <= y1 + 0.01:
            u = (y - y0) / max(y1 - y0, 1)
            h = hl + (hc - hl) * u
            esp = max(1.2, h * 0.5 * dens)
            top = int(math.floor(y - h * 2.2)) - 1
            hh = int(math.ceil(y)) - top + 2
            im = Image.new("RGBA", (self.zw * 2, hh), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            x = rng.uniform(0, esp)
            k = 0
            while x < self.zw:
                hueco = False
                if bloques:
                    b, g = bloques
                    hueco = (k % (b + g)) >= b
                if not hueco:
                    jx = x + rng.uniform(-0.15, 0.15) * esp
                    bnd = BANDERAS.get(tipo) if (cada and h > 6 and k % cada == 0) else None
                    for off in (0, self.zw):
                        _soldado(d, jx + off, y - top, h * rng.uniform(0.92, 1.06), tipo, rng, bnd)
                x += esp
                k += 1
            arr = np.asarray(im).astype(np.float32)
            nb = (1 - u) ** 1.4 * 0.85                       # bruma de distancia
            arr[..., :3] = arr[..., :3] * (1 - nb) + bruma * nb
            strip = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
            self.filas.append((strip.convert("RGB"), strip.getchannel("A"), top, h, j, u))
            y += max(1.0, h * 0.34 * dens)
            j += 1
        self.clip = None
        if cfg.get("poligono"):
            m = Image.new("L", (W, H), 0)
            ImageDraw.Draw(m).polygon([tuple(p) for p in cfg["poligono"]], fill=255)
            self.clip = m

    def __call__(self, img, alpha, cfg, t, i=0):
        for rgb, a, top, h, j, u in self.filas:
            o = int((-t * self.avance * (0.25 + 0.75 * u)) % self.zw)
            dy = int(round(math.sin(t * 6.5 + j * 0.9) * h * 0.05)) if (h > 8 and self.marcha) else 0
            box = (o, 0, o + self.zw, rgb.height)
            r, m = rgb.crop(box), a.crop(box)
            if self.clip is not None:
                cm = self.clip.crop((self.x0, top + dy, self.x0 + self.zw, top + dy + rgb.height))
                m = Image.fromarray(np.minimum(np.asarray(m), np.asarray(cm)))
            img.paste(r, (self.x0, top + dy), m)
            alpha.paste(255, (self.x0, top + dy, self.x0 + self.zw, top + dy + rgb.height), m)


def dibuja_estandarte(img, alpha, cfg, t, i=0):
    x, y = cfg["pos"]
    alto, ancho = cfg.get("alto", 60), cfg.get("ancho", 26)
    c1, c2 = tuple(cfg.get("color", (164, 38, 30))), tuple(cfg.get("color2", (190, 148, 64)))
    ph = cfg.get("fase", i * 1.3)
    d, dm = ImageDraw.Draw(img), ImageDraw.Draw(alpha)
    top = y - alto
    fh = ancho * 0.7
    n = 14
    sup, inf = [], []
    for k in range(n + 1):
        u = k / n
        wave = math.sin(u * 5 - t * 5 + ph) * fh * 0.14 * u
        sup.append((x + 1 + u * ancho, top + 2 + wave))
        inf.append((x + 1 + u * ancho * 0.96, top + 2 + fh + wave * 1.2 + u * 2))
    poly = sup + inf[::-1]
    for g, a, b, pole, fin in ((d, c1, c2, (86, 64, 36), (210, 170, 80)), (dm, 255, 255, 255, 255)):
        g.line([(x, top - 3), (x, y)], fill=pole, width=2)
        g.polygon(poly, fill=a)
        g.line(inf, fill=b, width=1)
        g.line(sup, fill=b, width=1)
        g.ellipse([x - 2, top - 6, x + 2, top - 2], fill=fin)
    # símbolo al centro de la tela
    cx = x + 1 + ancho * 0.5
    cy = top + 2 + fh * 0.5 + math.sin(0.5 * 5 - t * 5 + ph) * fh * 0.07
    r = fh * 0.26
    sim = cfg.get("simbolo", "nada")
    if sim == "sol":
        d.ellipse([cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6], fill=c2)
        for k in range(8):
            a = k * math.pi / 4
            d.line([(cx + math.cos(a) * r * 0.7, cy + math.sin(a) * r * 0.7), (cx + math.cos(a) * r, cy + math.sin(a) * r)], fill=c2)
    elif sim == "rueda":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c2)
        for k in range(6):
            a = k * math.pi / 3
            d.line([(cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r)], fill=c2)
    elif sim == "aguila":
        d.polygon([(cx - r * 1.3, cy - r * 0.5), (cx, cy + r * 0.2), (cx + r * 1.3, cy - r * 0.5), (cx + r * 0.4, cy + r * 0.3),
                   (cx + r * 0.2, cy + r), (cx - r * 0.2, cy + r), (cx - r * 0.4, cy + r * 0.3)], fill=c2)
        d.ellipse([cx - r * 0.25, cy - r * 0.55, cx + r * 0.25, cy - r * 0.05], fill=c2)
    elif sim == "dragon":
        pts = [(cx - r * 1.2 + k * r * 0.24, cy + math.sin(k * 0.9) * r * 0.6) for k in range(11)]
        d.line(pts, fill=c2, width=2)
        d.ellipse([pts[-1][0] - 2, pts[-1][1] - 2, pts[-1][0] + 2, pts[-1][1] + 2], fill=c2)
