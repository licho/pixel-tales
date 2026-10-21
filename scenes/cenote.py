"""Interior de un cenote, con la cámara a ras del agua: arriba la bóveda de caliza con la abertura al cielo,
raíces colgando y rayos de luz; abajo el agua turquesa vista por dentro, cada vez más oscura hacia el fondo.

Todo lo que se dibuja bajo el agua (actores incluidos) se tiñe y se pierde con la profundidad, y le pasan
encima reflejos de luz (cáusticas) que se mueven.

Parámetros:
  agua       fracción de H donde está la superficie (default 0.46)
  turbidez   0-1 qué tan rápido se pierde la vista con la profundidad (default 0.55)
  rayos      bool  rayos de luz desde la abertura (default true)
  raices     bool  (default true)
  gotas      bool  gotas cayendo que hacen ondas en la superficie (default false)
  hora       'dia' | 'tarde' | 'noche'  (default dia)
  semilla    int

Puntos útiles (vertical 256x384, agua 0.46 => superficie y≈177):
  tronco/serpiente en el fondo: sprite tzukan/tronco pos [128, 330], escala 1.0 (contraluz: false)
  ojos en el fondo: ojos pos [x, 300-330] (se ven a través del agua)
  algo justo bajo la superficie: y 0.50-0.60 H
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.pintura import roca
from pixel_tales.scene import Scene

AGUA_TOP = np.array([34, 120, 124], np.float32)
AGUA_FONDO = np.array([6, 26, 34], np.float32)


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.1, "far": 0.25, "mid": 0.5, "fg": 1.1}

    def build(self):
        W, H = self.W, self.H
        p = self.p
        xx, yy = self.grid()
        rng = np.random.default_rng(110 + self.seed)
        hora = p.get("hora", "dia")
        luz = {"dia": 1.0, "tarde": 0.8, "noche": 0.25}[hora]
        self.wy = wy = float(p.get("agua", 0.46)) * H
        ox, oy, orx, ory = 0.52 * W, 0.0, 0.30 * W, 0.075 * H        # abertura al cielo
        self.ab = (ox, oy, orx, ory)

        # ---- fondo: pared lejana de la caverna + cielo por la abertura
        pared = roca(self, (70, 66, 56), self.seed, 0.4) * 0.5
        cielo = np.array([150, 200, 210] if hora == "dia" else [230, 160, 100] if hora == "tarde" else [30, 40, 70], np.float32)
        hueco = ((xx - ox) / orx) ** 2 + ((yy - oy) / ory) ** 2 < 1
        sky = pared.copy()
        sky[hueco] = cielo
        # selva asomando en el borde del hueco
        sel = hueco & (vnoise(W, H, 3, 7 + self.seed) > 0.5) & (((xx - ox) / orx) ** 2 + ((yy - oy) / ory) ** 2 > 0.45)
        sky[sel] = (44, 72, 34)
        # luz que baña la pared cerca de la abertura
        dd = np.hypot((xx - ox) / W, (yy - oy) / H)
        sky *= (0.45 + 1.2 * np.exp(-dd / 0.35) * luz)[..., None]
        sky[hueco] = cielo
        self.sky = sky

        # ---- capa principal: paredes laterales, bóveda, estalactitas, raíces, agua
        img = Image.new("RGB", (W, H))
        mk = Image.new("L", (W, H), 0)
        d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mk)
        # paredes: bordes irregulares izq/der que se cierran arriba (bóveda)
        izq, der = [(0, H), (0, 0)], [(W, H), (W, 0)]
        for y in np.linspace(0, H, 40):
            v = y / H
            ancho = 0.24 * W * (1 - 0.8 * math.sin(min(v / 0.6, 1) * math.pi / 2)) + 0.05 * W
            ancho += rng.uniform(-3, 3) + 6 * math.sin(v * 17 + self.seed)
            izq.append((ancho, y))
            der.append((W - ancho - 4 * math.sin(v * 11), y))
        izq.append((0, H))
        der.append((W, H))
        roca_m = roca(self, (120, 110, 90), self.seed + 5, 0.75)
        m_par = Image.new("L", (W, H), 0)
        dp = ImageDraw.Draw(m_par)
        dp.polygon(izq, fill=255)
        dp.polygon(der, fill=255)
        # bóveda: todo lo de arriba menos la abertura
        dp.rectangle([0, 0, W, 0.03 * H], fill=255)
        for x in np.arange(0, W, 5):                             # estalactitas desde la bóveda
            if abs(x - ox) < orx * 0.95:
                continue
            L = rng.uniform(4, 24)
            dp.polygon([(x, 0), (x + rng.uniform(3, 7), 0), (x + rng.uniform(1, 4), L)], fill=255)
        dp.ellipse([ox - orx * 1.25, -ory * 1.6, ox + orx * 1.25, ory * 1.6], fill=255)
        dp.ellipse([ox - orx, -ory, ox + orx, ory], fill=0)
        pmask = np.asarray(m_par) > 0
        alb = pared.copy() * 0.9                                 # pared lejana (en esta capa para que le caigan los rayos)
        alb[pmask] = roca_m[pmask]
        # borde de la abertura más claro (iluminado)
        borde = pmask & (np.hypot((xx - ox) / orx, (yy - oy) / ory) < 1.5)
        alb[borde] *= 1.25

        # agua: albedo base (degradado) y fondo rocoso
        v = np.clip((yy - wy) / (H - wy), 0, 1)
        agua = AGUA_TOP * (1 - v[..., None]) + AGUA_FONDO * v[..., None]
        under = yy >= wy
        alb[under] = agua[under]
        fondo = Image.new("L", (W, H), 0)
        df = ImageDraw.Draw(fondo)
        pts = [(0, H)] + [(x, 0.86 * H + 10 * math.sin(x * 0.05 + self.seed) + rng.uniform(-3, 3)) for x in range(0, W + 8, 8)] + [(W, H)]
        df.polygon(pts, fill=255)
        for _ in range(9):
            x, y = rng.uniform(0, W), rng.uniform(0.80, 0.95) * H
            r = rng.uniform(8, 22)
            df.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=255)
        fm = np.asarray(fondo) > 0
        alb[fm] = roca(self, (90, 96, 80), self.seed + 9, 0.8)[fm]
        self.mid_alb = alb
        self.mid_a = ~hueco
        self.mid_em[hueco & False] = 0

        # raíces colgando desde la abertura hasta el agua
        if p.get("raices", True):
            rm = Image.new("L", (W, H), 0)
            dr = ImageDraw.Draw(rm)
            for _ in range(14):
                x0 = ox + rng.uniform(-0.9, 0.9) * orx
                y0 = oy + ory * rng.uniform(0.3, 0.9)
                L = rng.uniform(0.2, 1.0) * (wy - y0) + 4
                pts = [(x0 + 2 * math.sin(k * 0.6 + x0) * k / 6, y0 + L * k / 12) for k in range(13)]
                dr.line(pts, fill=255, width=1 if rng.random() < 0.7 else 2)
            r_m = np.asarray(rm) > 0
            self.mid_alb[r_m] = (52, 40, 28)
            self.mid_a |= r_m

        # rayos de luz: bandas diagonales desde la abertura
        self.rayos = np.zeros((H, W), np.float32)
        if p.get("rayos", True) and hora != "noche":
            for k in range(6):
                x0 = ox + (k / 5 - 0.5) * orx * 1.6
                ang = 0.18 + rng.uniform(-0.05, 0.05)
                w = rng.uniform(6, 15)
                dx = xx - (x0 + (yy - oy) * ang)
                band = np.exp(-(dx / w) ** 2) * np.clip(1 - yy / (H * 0.95), 0, 1)
                self.rayos += band * rng.uniform(0.5, 1.0)
            self.rayos *= (0.6 + 0.4 * fbm(W, H, 120 + self.seed, (24, 12)))
        self.luz = luz
        self.caus = vnoise(W, H, 6, 130 + self.seed)
        self.caus2 = vnoise(W, H, 4, 131 + self.seed)
        self.gotas = p.get("gotas", False)
        self.turb = float(p.get("turbidez", 0.55))
        self.rng_g = np.random.default_rng(140 + self.seed)
        self.gotas_xy = [(self.rng_g.uniform(0.15, 0.85) * W, self.rng_g.uniform(0, 1.6)) for _ in range(7)]

        self.lights.append(Light("abertura", self.point(ox, wy * 0.8, 0.9 * H, 0.75 * luz), (0.85, 1.0, 0.95)))
        self.lights.append(Light("agua", self.pool(ox, wy, 0.6 * W, 0.08 * H, 0.35 * luz), (0.5, 0.95, 0.9)))

    def animar(self, col, t):
        W, H = self.W, self.H
        xx, yy = self.grid()
        wy = self.wy
        u = yy >= wy
        v = np.clip((yy - wy) / (H - wy), 0, 1)
        # bajo el agua: se pierde con la profundidad hacia el color del agua
        k = np.clip(v ** 1.4 * (0.35 + 0.7 * self.turb), 0, 0.9)
        agua = AGUA_TOP * (1 - v[..., None]) + AGUA_FONDO * v[..., None]
        mix = k[..., None]
        col[u] = col[u] * (1 - mix[u]) * np.array([0.55, 0.9, 0.95], np.float32) + agua[u] * mix[u] * self.luz + agua[u] * 0.15
        # cáusticas que se mueven
        c = np.sin(self.caus * 18 + t * 1.3) * np.sin(self.caus2 * 15 - t * 1.0)
        cm = u & (c > 0.72)
        col[cm] += (35 * (1 - v[cm]) * self.luz)[..., None] * np.array([0.7, 1.0, 0.95], np.float32)
        # superficie: línea brillante con ondas
        s = np.abs(yy - wy) < 1.5 + 1.5 * np.sin(xx * 0.15 + t * 2)
        col[s] = col[s] * 0.6 + np.array([110, 190, 180], np.float32) * 0.4 * (0.5 + 0.5 * self.luz)
        # rayos de luz (volumétricos, tiemblan un poco)
        if self.rayos.any():
            r = self.rayos * (0.85 + 0.15 * math.sin(t * 0.8))
            r = r * np.where(u, 0.6, 1.0)
            col += (r * 95 * self.luz)[..., None] * np.array([0.85, 1.0, 0.9], np.float32)
        # gotas: anillos que se abren en la superficie
        if self.gotas:
            for gx, t0 in self.gotas_xy:
                age = (t + t0) % 1.6
                rr = 2 + age * 22
                ring = (np.abs(np.hypot((xx - gx), (yy - wy) * 5) - rr) < 1.2) & (np.abs(yy - wy) < 6)
                col[ring] = col[ring] * 0.4 + np.array([200, 240, 230], np.float32) * 0.6 * (1 - age / 1.6)
