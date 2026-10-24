"""Ruinas de un castillo bajo la luna llena: muro con un gran arco, torres rotas con musgo, árbol seco,
rocas, escalones bajo el arco y un camino de tierra iluminado por la luna. Fantasía oscura.

Parámetros:
  luna       [x, y] relativos (default [0.36, 0.15])
  nubes      0-1 cantidad de nubes (default 0.7)
  arbol      bool  árbol seco a la izquierda (default true)
  antorchas  bool  antorchas a los lados del arco (default false)
  semilla    int

Puntos útiles (relativos a W x H; pies):
  bajo el arco / en los escalones: (0.53 W, 0.80 H) personaje de ~0.18 H
  camino cerca: (0.5 W, 0.95 H) personaje de ~0.35 H
  murciélagos: zona [0.4 W, 0.05 H, 0.95 W, 0.45 H]
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.pintura import antorcha, estrellas, piedra_bloques, roca
from pixel_tales.scene import Scene


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.08, "far": 0.2, "mid": 0.55, "fg": 1.2}

    def build(self):
        W, H = self.W, self.H
        p = self.p
        xx, yy = self.grid()
        rng = np.random.default_rng(150 + self.seed)
        S = min(W, H)                                   # escala base
        mx, my = (f * d for f, d in zip(p.get("luna", [0.36, 0.15]), (W, H)))
        mr = 0.085 * S

        # ---------------------------------------------------------------- cielo con luna y nubes
        t = (yy / H)[..., None]
        sky = np.array([24, 30, 40], np.float32) * (1 - t) + np.array([60, 70, 84], np.float32) * t
        estrellas(self, sky, 0.002, 0.4, self.seed, (190, 200, 200))
        dd = np.hypot(xx - mx, yy - my)
        sky += (np.exp(-dd / (0.35 * S)) * 50)[..., None] * np.array([0.8, 0.9, 0.85], np.float32)
        luna = dd < mr
        sky[luna] = (236, 242, 226)
        sky[luna & (np.hypot(xx - mx - mr * 0.3, yy - my + mr * 0.2) < mr * 0.35)] = (214, 224, 210)
        # nubes: bandas horizontales de ruido, cuerpo oscuro y bordes iluminados cerca de la luna
        nub = fbm(W, H, 160 + self.seed, (64, 32, 16, 8))
        estir = np.repeat(fbm(W // 3 + 1, H, 161 + self.seed, (16, 8, 4)), 3, axis=1)[:, :W]
        c = nub * 0.45 + estir * 0.55
        dens = float(p.get("nubes", 0.7))
        alto = smooth(0.0, 0.25, yy / H) * (1 - smooth(0.55, 0.75, yy / H))
        cuerpo = smooth(0.58 - 0.16 * dens, 0.66 - 0.16 * dens, c) * (0.25 + 0.75 * alto)
        borde = np.clip(cuerpo - np.roll(cuerpo, 2, 0), 0, 1)              # parte de arriba de cada nube
        cerca = np.exp(-dd / (0.45 * S))
        nube_col = np.array([46, 54, 66], np.float32) + (cerca * 60)[..., None] * np.array([0.9, 1.0, 0.9], np.float32)
        sky = sky * (1 - cuerpo[..., None]) + nube_col * cuerpo[..., None]
        sky += (borde * (60 + 150 * cerca))[..., None] * np.array([0.85, 0.95, 0.85], np.float32)
        frente = cuerpo > 0.5                                                # nubes delante de la luna
        sky[luna & frente] = sky[luna & frente] * 0.5 + np.array([200, 212, 200], np.float32) * 0.5
        self.sky = sky

        # ---------------------------------------------------------------- fondo: línea de árboles lejanos
        far = Image.new("L", (W, H), 0)
        fd = ImageDraw.Draw(far)
        base = 0.78 * H
        x = -4.0
        while x < W + 4:
            r = rng.uniform(0.02, 0.05) * S
            fd.ellipse([x - r, base - r * rng.uniform(1.0, 2.2), x + r, base + 4], fill=255)
            x += r * 1.2
        fd.rectangle([0, base, W, H], fill=255)
        self.far_a = np.asarray(far) > 0
        self.far = np.broadcast_to(np.array([30, 36, 46], np.float32), (H, W, 3)).copy()

        # ---------------------------------------------------------------- ruinas
        piedra = piedra_bloques(self, (62, 64, 72), max(5, int(0.035 * S)), max(3, int(0.018 * S)), self.seed)
        piedra2 = piedra_bloques(self, (56, 58, 66), max(4, int(0.025 * S)), max(3, int(0.016 * S)), self.seed + 1)
        img_m = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(img_m)
        P = lambda fx, fy: (fx * W, fy * H)
        suelo = 0.80
        # muro bajo a la izquierda (roto)
        d.polygon([P(0.20, suelo), P(0.20, 0.55), P(0.25, 0.53), P(0.28, 0.56), P(0.33, 0.52), P(0.38, 0.54),
                   P(0.40, 0.46), P(0.42, suelo)], fill=255)
        # bloque central con el arco y torre
        d.polygon([P(0.40, suelo), P(0.40, 0.38), P(0.43, 0.34), P(0.46, 0.36), P(0.48, 0.30), P(0.55, 0.22),
                   P(0.57, 0.19), P(0.66, 0.19), P(0.68, 0.24), P(0.67, 0.40), P(0.70, 0.44), P(0.70, suelo)], fill=255)
        # muro derecho y torre alta
        d.polygon([P(0.68, suelo), P(0.68, 0.46), P(0.72, 0.44), P(0.76, 0.47), P(0.80, 0.43), P(0.82, 0.30),
                   P(0.82, suelo)], fill=255)
        d.polygon([P(0.81, suelo + 0.02), P(0.82, 0.18), P(0.85, 0.14), P(0.90, 0.13), P(0.93, 0.16), P(0.93, 0.30),
                   P(0.95, suelo + 0.02)], fill=255)
        muro = np.asarray(img_m) > 0
        # arco (hueco al cielo) y ventanas
        ax, aw, atop = 0.535 * W, 0.075 * W, 0.53 * H
        arco = (((xx - ax) / aw) ** 2 + ((yy - atop) / (aw * 0.95)) ** 2 < 1) & (yy < atop) | \
               ((np.abs(xx - ax) < aw) & (yy >= atop) & (yy < suelo * H))
        vent = np.zeros_like(muro)
        for vx, vy, vw in ((0.535, 0.38, 0.018), (0.745, 0.55, 0.014), (0.875, 0.25, 0.012)):
            cx, cy, ww = vx * W, vy * H, vw * W
            vent |= (((xx - cx) / ww) ** 2 + ((yy - cy) / ww) ** 2 < 1) & (yy < cy) | ((np.abs(xx - cx) < ww) & (yy >= cy) & (yy < cy + ww * 3.2))
        alb = np.zeros((H, W, 3), np.float32)
        torre_d = (xx > 0.81 * W)
        alb[muro] = np.where(torre_d[muro][:, None], piedra2[muro] * 1.1, piedra[muro])
        # luz de luna desde arriba a la izquierda: caras izquierdas más claras, borde del arco iluminado
        lit = muro & (np.roll(~muro, -2, 1) | np.roll(~muro, -3, 1) | np.roll(~muro, 1, 0))     # bordes derechos y de arriba
        alb[lit] = alb[lit] * 0.7 + np.array([170, 176, 176], np.float32) * 0.45
        ruido_luz = fbm(W, H, 172 + self.seed, (24, 12, 6))
        alb[muro] *= (0.75 + 0.5 * ruido_luz[muro])[..., None]
        borde_arco = muro & (np.roll(arco, -2, 1) & ~arco)
        alb[borde_arco] = alb[borde_arco] * 0.6 + np.array([200, 206, 200], np.float32) * 0.4
        # pilastras a los lados del arco
        for s in (-1, 1):
            pil = muro & (np.abs(xx - (ax + s * (aw + 0.012 * W))) < 0.011 * W) & (yy > atop - aw) & (yy < suelo * H)
            alb[pil] = alb[pil] * 0.6 + np.array([130, 134, 140], np.float32) * 0.6
        # sombra fuerte en la parte de abajo y a la derecha de las torres
        sh = smooth(0.45 * H, suelo * H, yy) * 0.35
        alb[muro] *= (1 - sh[muro])[..., None]
        # musgo en los bordes de arriba y colgando
        mus = muro & np.roll(~muro, 2, 0) & (vnoise(W, H, 2, 170 + self.seed) > 0.45)
        cuelga = muro & (fbm(W, H, 171 + self.seed, (4, 2)) > 0.72) & (yy < 0.6 * H)
        alb[mus | cuelga] = alb[mus | cuelga] * 0.4 + np.array([70, 96, 48], np.float32) * 0.6
        alb[vent] = (14, 16, 22)
        a = muro & ~arco
        self.arco = (ax, aw, atop)

        # escalones bajo el arco
        img = Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8))
        dr = ImageDraw.Draw(img)
        mk = Image.fromarray((a * 255).astype(np.uint8))
        dm = ImageDraw.Draw(mk)
        for k in range(4):
            y0 = suelo * H - k * 0.012 * H
            w = aw * (1.25 - k * 0.06)
            dr.rectangle([ax - w, y0 - 0.012 * H, ax + w, y0], fill=(118, 124, 126) if k % 2 else (96, 100, 104))
            dm.rectangle([ax - w, y0 - 0.012 * H, ax + w, y0], fill=255)
            dr.line([(ax - w, y0 - 0.012 * H), (ax + w, y0 - 0.012 * H)], fill=(160, 168, 166))

        # suelo y camino iluminado
        suelo_m = yy >= suelo * H - 1
        arr = np.asarray(img, np.float32).copy()
        tierra = roca(self, (70, 62, 50), self.seed + 4, 0.6, grietas=False)
        camino = np.exp(-(((xx - 0.5 * W) / (0.32 * W)) ** 2 + ((yy - 0.92 * H) / (0.10 * H)) ** 2))
        tierra = tierra * (0.45 + 1.2 * camino)[..., None] * np.array([1.0, 0.95, 0.85], np.float32)
        arr[suelo_m] = tierra[suelo_m]
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        dr = ImageDraw.Draw(img)
        dm.rectangle([0, suelo * H - 1, W, H], fill=255)
        for _ in range(60):                                                    # piedritas en el camino
            x, y = rng.uniform(0.2, 0.8) * W, rng.uniform(0.84, 1.0) * H
            r = rng.uniform(0.003, 0.009) * S
            dr.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(40, 40, 44))

        # rocas: montones a los lados y bloques en primer plano
        def roca_poly(cx, cy, r, sem):
            rr = np.random.default_rng(sem)
            n = 7
            pts = [(cx + math.cos(k / n * 2 * math.pi) * r * rr.uniform(0.75, 1.15),
                    cy + math.sin(k / n * 2 * math.pi) * r * 0.62 * rr.uniform(0.75, 1.15)) for k in range(n)]
            dr.polygon(pts, fill=(64, 66, 72))
            top = [q for q in pts if q[1] <= cy] + [(cx + r * 0.6, cy), (cx - r * 0.6, cy)]
            dr.polygon([(cx - r * 0.7, cy - r * 0.15), (cx - r * 0.2, cy - r * 0.6), (cx + r * 0.6, cy - r * 0.45), (cx + r * 0.3, cy - r * 0.05)],
                       fill=(150, 156, 162))
            dr.line(pts + [pts[0]], fill=(30, 32, 38))
            dm.polygon(pts, fill=255)
        for k in range(16):                                                    # escombros al pie de las ruinas
            side = 0.28 if k % 2 else 0.74
            roca_poly(rng.uniform(side - 0.10, side + 0.12) * W, rng.uniform(0.74, 0.84) * H, rng.uniform(0.02, 0.05) * S, 200 + k)
        for k, (fx, fy, fr) in enumerate(((0.06, 0.97, 0.10), (0.24, 0.84, 0.07), (0.88, 0.95, 0.11), (0.72, 0.92, 0.06),
                                          (0.38, 1.0, 0.06), (0.98, 0.86, 0.06))):
            roca_poly(fx * W, fy * H, fr * S, 300 + k)
        # matorrales rojizos a los lados
        for fx, fy, fr in ((0.02, 0.70, 0.08), (0.97, 0.66, 0.07)):
            for _ in range(20):
                x, y = fx * W + rng.uniform(-fr, fr) * S, fy * H + rng.uniform(-fr, fr) * S * 0.8
                r = rng.uniform(0.01, 0.025) * S
                dr.ellipse([x - r, y - r, x + r, y + r], fill=(64, 32, 36) if rng.random() < 0.6 else (44, 24, 26))
                dm.ellipse([x - r, y - r, x + r, y + r], fill=255)
        # pasto seco
        for _ in range(80):
            x, y = rng.uniform(0, W), rng.uniform(0.78, 0.98) * H
            h = rng.uniform(2, 6)
            dr.line([(x, y), (x + rng.uniform(-1.5, 1.5), y - h)], fill=(120, 96, 60))

        # árbol seco: ramas recursivas
        if p.get("arbol", True):
            def rama(x, y, ang, largo, grosor, nivel):
                x2, y2 = x + math.cos(ang) * largo, y + math.sin(ang) * largo
                dr.line([(x, y), (x2, y2)], fill=(44, 30, 26), width=max(1, int(grosor)))
                dm.line([(x, y), (x2, y2)], fill=255, width=max(1, int(grosor)))
                if grosor > 1.5:                                               # borde iluminado
                    dr.line([(x + grosor * 0.4, y), (x2 + grosor * 0.4, y2)], fill=(120, 96, 76))
                if nivel <= 0 or largo < 2:
                    return
                for da in (rng.uniform(-0.8, -0.3), rng.uniform(0.25, 0.7)):
                    rama(x2, y2, ang + da, largo * rng.uniform(0.6, 0.78), grosor * 0.62, nivel - 1)
            tx, ty = 0.13 * W, 0.80 * H
            dr.polygon([(tx - 0.03 * S, ty), (tx + 0.03 * S, ty), (tx + 0.015 * S, ty - 0.2 * H), (tx - 0.01 * S, ty - 0.2 * H)], fill=(58, 40, 32))
            dm.polygon([(tx - 0.03 * S, ty), (tx + 0.03 * S, ty), (tx + 0.015 * S, ty - 0.2 * H), (tx - 0.01 * S, ty - 0.2 * H)], fill=255)
            rama(tx + 0.002 * W, ty - 0.2 * H, -1.35, 0.13 * H, 0.03 * S, 5)
            rama(tx, ty - 0.17 * H, -2.4, 0.10 * H, 0.022 * S, 4)
            rama(tx + 0.01 * W, ty - 0.14 * H, -0.45, 0.11 * H, 0.02 * S, 4)

        self.mid_alb = np.asarray(img, np.float32).copy()
        self.mid_a = np.asarray(mk) > 0
        if p.get("antorchas"):
            for s in (-1, 1):
                antorcha(self, ax + s * (aw + 0.03 * W), 0.62 * H, tam=0.03 * S, radio=0.012 * S * 10, intensidad=0.9)
        self.lights.append(Light("luna", self.point(mx, my, 1.1 * S, 0.45), (0.75, 0.82, 0.9)))
        self.lights.append(Light("camino", self.pool(0.5 * W, 0.92 * H, 0.35 * W, 0.08 * H, 0.35), (0.9, 0.88, 0.75)))
