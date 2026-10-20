"""Río subterráneo que serpentea hacia el fondo de una caverna. Sirve como río/lago en otras historias.

Parámetros:
  agua       'sangre' | 'pus' | 'agua' | 'noche' | [r, g, b]   (default sangre)
  brillo     qué tanto brilla el agua por sí sola, 0-1 (default 0.35)
  antorcha   bool, antorcha en la orilla izquierda (default true)
  semilla    int

Puntos útiles (relativos a W x H):
  orilla izquierda: x 0.02-0.28 W, y 0.75-0.97 H      orilla derecha: x 0.72-0.98 W, y 0.75-0.97 H
  zona para escorpiones: [0.02 W, 0.80 H, 0.30 W, 0.97 H] y [0.70 W, 0.80 H, 0.98 W, 0.97 H]
"""
import math

import numpy as np

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.pintura import antorcha, estalactitas, niebla_profundidad, roca
from pixel_tales.scene import Scene

AGUAS = {"sangre": (96, 14, 14), "pus": (150, 140, 60), "agua": (30, 56, 60), "noche": (24, 40, 50)}


class Escena(Scene):
    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        agua = p.get("agua", "sangre")
        self.agua = np.array(AGUAS.get(agua, agua) if isinstance(agua, str) else agua, np.float32)
        vx, vy = 0.5 * W, 0.36 * H

        d = np.hypot((xx - vx) / W, (yy - vy) / H)
        self.sky = np.array([6, 4, 6], np.float32) + (self.agua * 0.9) * (np.exp(-d / 0.07) * 0.35)[..., None]

        # caverna: roca alrededor, abertura al fondo
        n = vnoise(W, H, 6, 60 + self.seed)
        opening = ((((xx - vx) / (0.16 * W)) ** 2 + ((yy - vy) / (0.07 * H)) ** 2) < 1 + 0.6 * (n - 0.5)) & (yy < vy + 0.02 * H)
        alb = roca(self, (56, 44, 40), self.seed + 3)
        alb[yy < vy - 0.06 * H] *= 0.65

        # orillas de tierra/piedra
        ground = yy > vy + 0.01 * H
        tierra = roca(self, (74, 58, 44), self.seed + 9, 0.5, grietas=False)
        alb[ground] = tierra[ground]

        # río serpenteando: centro y ancho según la profundidad
        pz = np.clip((yy - vy) / (H - vy), 0.001, 1)              # 0 lejos, 1 cerca
        cx = vx + np.sin(3.2 / (pz + 0.25)) * 0.12 * W * pz
        half = 0.03 * W + 0.30 * W * pz ** 1.3
        river = ground & (np.abs(xx - cx) < half * (1 + 0.08 * (n - 0.5)))
        self.river, self.pz, self.cx = river, pz, cx
        self.flow_noise = fbm(W, H, 77 + self.seed, (16, 8, 4))
        alb[river] = self.agua
        bank = ground & ~river & (np.abs(xx - cx) < half + 2 + 3 * pz)
        alb[bank] *= 0.6                                          # orilla mojada

        # rocas en las orillas
        rng = np.random.default_rng(12 + self.seed)
        rocks = np.zeros((H, W), bool)
        for _ in range(26):
            ry = rng.uniform(vy + 0.05 * H, H)
            pr = (ry - vy) / (H - vy)
            side = rng.choice([-1, 1])
            c = vx + math.sin(3.2 / (pr + 0.25)) * 0.12 * W * pr
            hw = 0.03 * W + 0.30 * W * pr ** 1.3
            rx = c + side * (hw + rng.uniform(4, 0.3 * W) * pr + 2)
            r = (2 + 10 * pr) * rng.uniform(0.6, 1.4)
            rocks |= ((xx - rx) / r) ** 2 + ((yy - ry) / (r * 0.6)) ** 2 < 1
        alb[rocks] = roca(self, (90, 80, 70), self.seed + 5, 0.5, grietas=False)[rocks]

        niebla_profundidad(self, alb, vx, vy, 0.30, 0.05)
        self.mid_alb, self.mid_a = alb, ~opening
        self.mid_em[river] = self.agua * float(p.get("brillo", 0.15)) * (0.4 + 0.6 * pz[river])[..., None]

        self.lights.append(Light("rio", self.point(vx, 0.75 * H, 0.35 * W, 0.5), tuple(self.agua / 140)))
        if p.get("antorcha", True):
            antorcha(self, 0.12 * W, 0.55 * H, 1.3, radio=42)

        def fg(dr):
            dr.rectangle([0, 0, W, 0.015 * H], fill=255)
            estalactitas(self, dr, 0.015 * H, 0, W, 0.16 * H, self.seed + 1)
        self.fg_a = self.mask(fg)
        self.fg_alb[:] = (30, 22, 22)

    def animar(self, col, t):
        """Ondas que corren hacia la cámara."""
        r = self.river
        _, yy = self.grid()
        ph = yy[r] * (0.5 / (self.pz[r] + 0.3)) - t * 3.0 + self.flow_noise[r] * 2.5
        wave = np.sin(ph)
        hi = (wave > 0.94)[..., None]
        lo = (wave < -0.5)[..., None]
        c = col[r]
        c = np.where(hi, c * 1.6 + self.agua * 0.35 + 6, c)
        c = np.where(lo, c * 0.8, c)
        col[r] = c
