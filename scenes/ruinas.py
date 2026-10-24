"""Ruinas de un castillo bajo la luna llena: muro con un gran arco, torres rotas con musgo, árbol seco,
rocas, escalones bajo el arco y un camino de tierra iluminado por la luna. Fantasía oscura.

Versión detallada: piedra en bloques irregulares con bisel y huecos, siluetas desmoronadas, nubes con volumen
(panza oscura y bordes plateados), rocas y árbol sombreados con mapa de alturas, musgo y enredaderas.

Parámetros:
  luna       [x, y] relativos (default [0.36, 0.15])
  nubes      0-1 cantidad de nubes (default 0.75)
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
from pixel_tales.pintura import antorcha, estrellas
from pixel_tales.scene import Scene
from pixel_tales.volumen import bloques, bordes, nubes_volumen, pintar_bloques, sombrear

LUZ = (-0.55, -0.7, 0.5)            # la luna está arriba a la izquierda


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.08, "far": 0.2, "mid": 0.55, "fg": 1.2}

    def m(self, fn):
        im = Image.new("L", (self.W, self.H), 0)
        fn(ImageDraw.Draw(im))
        return np.asarray(im) > 127

    def build(self):
        W, H = self.W, self.H
        p = self.p
        xx, yy = self.grid()
        rng = np.random.default_rng(150 + self.seed)
        S = min(W, H)
        mx, my = (f * d for f, d in zip(p.get("luna", [0.36, 0.15]), (W, H)))
        mr = 0.085 * S
        P = lambda fx, fy: (fx * W, fy * H)
        suelo = 0.80

        # ================================================================ cielo
        t = (yy / H)[..., None]
        sky = np.array([18, 22, 32], np.float32) * (1 - t) + np.array([54, 62, 78], np.float32) * t
        estrellas(self, sky, 0.0025, 0.35, self.seed, (190, 200, 205))
        dd = np.hypot(xx - mx, yy - my)
        sky += (np.exp(-dd / (0.30 * S)) * 60)[..., None] * np.array([0.78, 0.88, 0.84], np.float32)
        luna = dd < mr
        crat = fbm(W, H, 151 + self.seed, (6, 3))
        sky[luna] = np.array([236, 242, 226], np.float32) * (0.88 + 0.14 * crat[luna])[..., None]
        sky[luna & (dd > mr - 1.2)] *= 0.93
        dens = float(p.get("nubes", 0.75))
        # nubes de atrás (finas, alargadas) y nubes de adelante (grandes, con volumen)
        estir = np.repeat(fbm(W // 4 + 1, H, 161 + self.seed, (16, 8, 4, 2)), 4, axis=1)[:, :W]
        banda = np.exp(-((yy / H - 0.30) / 0.16) ** 2)
        d1 = estir * (0.55 + 0.6 * banda) + 0.12 * dens
        col1, a1 = nubes_volumen(d1, (mx, my), (30, 36, 50), (120, 132, 140), relieve=8, falloff=0.35, umbral=(0.70, 0.80))
        sky = sky * (1 - a1[..., None] * 0.35) + col1 * a1[..., None] * 0.35
        gran = fbm(W, H, 162 + self.seed, (40, 20, 10, 5, 2))
        masa = np.exp(-((yy / H - 0.34) / 0.12) ** 2) * (0.65 + 0.45 * smooth(0.1, 0.7, xx / W))
        masa += np.exp(-((yy / H - 0.08) / 0.07) ** 2) * 0.55 * smooth(0.45, 0.8, xx / W)
        d2 = gran * 0.75 + masa * 0.45 + 0.08 * dens
        col2, a2 = nubes_volumen(d2, (mx, my), (26, 30, 42), (224, 234, 216), relieve=22, falloff=0.55, umbral=(0.66, 0.70))
        sky = sky * (1 - a2[..., None]) + col2 * a2[..., None]
        delante = luna & (a2 > 0.5)                               # la luna se asoma entre nubes
        sky[delante] = sky[delante] * 0.55 + np.array([210, 220, 206], np.float32) * 0.45
        self.sky = sky

        # ================================================================ fondo: colinas y árboles en bruma
        far = Image.new("L", (W, H), 0)
        fd = ImageDraw.Draw(far)
        base = 0.785 * H
        x = -4.0
        while x < W + 4:
            r = rng.uniform(0.015, 0.045) * S
            fd.ellipse([x - r, base - r * rng.uniform(1.2, 2.6), x + r, base + 4], fill=255)
            x += r * 1.1
        fd.rectangle([0, base, W, H], fill=255)
        self.far_a = np.asarray(far) > 0
        bruma = smooth(0.62 * H, 0.80 * H, yy)
        self.far = (np.array([44, 52, 66], np.float32) * (1 - bruma[..., None] * 0.4)
                    * (0.85 + 0.25 * fbm(W, H, 163 + self.seed, (8, 4)))[..., None])

        # ================================================================ ruinas
        muro = self.m(lambda d: (
            d.polygon([P(0.20, suelo), P(0.20, 0.56), P(0.24, 0.535), P(0.28, 0.565), P(0.33, 0.52), P(0.38, 0.545),
                       P(0.40, 0.46), P(0.42, suelo)], fill=255),
            d.polygon([P(0.40, suelo), P(0.40, 0.38), P(0.43, 0.34), P(0.46, 0.36), P(0.48, 0.30), P(0.55, 0.22),
                       P(0.57, 0.185), P(0.66, 0.185), P(0.68, 0.24), P(0.67, 0.40), P(0.70, 0.44), P(0.70, suelo)], fill=255),
            d.polygon([P(0.68, suelo), P(0.68, 0.46), P(0.72, 0.44), P(0.76, 0.47), P(0.80, 0.43), P(0.82, 0.30),
                       P(0.82, suelo)], fill=255)))
        torre = self.m(lambda d: d.polygon([P(0.81, suelo + 0.02), P(0.82, 0.18), P(0.84, 0.15), P(0.90, 0.13),
                                            P(0.935, 0.16), P(0.935, 0.32), P(0.95, suelo + 0.02)], fill=255))
        ids, nb = bloques(W, H, (max(3, int(0.016 * S)), max(4, int(0.026 * S))), (max(5, int(0.03 * S)), max(8, int(0.06 * S))),
                          self.seed)
        # desmoronar la silueta: quitar bloques del borde superior
        todo = muro | torre
        for paso in range(3):
            fuera = ~todo
            borde_sup = todo & np.roll(fuera, 1, 0) & (yy < 0.72 * H)
            cand = np.unique(ids[borde_sup])
            quita = cand[rng.random(len(cand)) < 0.35]
            todo &= ~np.isin(ids, quita)
        muro &= todo
        torre &= todo
        ruido = fbm(W, H, 172 + self.seed, (24, 12, 6))
        piedra, hueco = pintar_bloques(ids, nb, (84, 86, 94), self.seed, faltan=0.07, ruido=ruido)
        piedra_t, _ = pintar_bloques(ids, nb, (74, 76, 86), self.seed + 3, faltan=0.05, ruido=ruido)
        # forma general con volumen (bordes redondeados, torres como cilindros)
        vol = sombrear(muro, (1, 1, 1), LUZ, radio=0.03 * S, relieve=0.05 * S, ambiente=0.45, brillo=0)
        vol_t = sombrear(torre, (1, 1, 1), LUZ, radio=0.05 * S, relieve=0.10 * S, ambiente=0.40, brillo=0)
        alb = np.zeros((H, W, 3), np.float32)
        alb[muro] = piedra[muro] * vol[muro]
        alb[torre] = piedra_t[torre] * vol_t[torre]
        # oscurece hacia la base y en la mitad derecha de cada masa (lado contrario a la luna)
        alb *= (1 - 0.35 * smooth(0.5 * H, suelo * H, yy))[..., None]
        # arco: hueco al cielo con intradós (grosor del muro) iluminado del lado derecho
        ax, aw, atop = 0.535 * W, 0.072 * W, 0.53 * H
        def dentro_arco(cx, w, top, extra=0):
            return ((((xx - cx) / (w + extra)) ** 2 + ((yy - top) / ((w + extra) * 0.95)) ** 2 < 1) & (yy < top)) | \
                   ((np.abs(xx - cx) < w + extra) & (yy >= top) & (yy < suelo * H))
        arco = dentro_arco(ax, aw, atop)
        dovelas = dentro_arco(ax, aw, atop, 0.022 * W) & ~arco & muro
        ang = np.arctan2(yy - atop, xx - ax)
        dov = (np.floor((ang + math.pi) / (math.pi / 11)) % 2 == 0)
        alb[dovelas] = np.where(dov[dovelas][:, None], 110, 92) * np.array([1.0, 1.0, 1.06], np.float32) * vol[dovelas]
        intrados = arco & (xx > ax + aw * 0.72)
        alb[intrados] = np.array([120, 124, 128], np.float32) * (0.8 + 0.3 * ruido[intrados])[..., None]
        intrados2 = arco & (xx < ax - aw * 0.80)
        alb[intrados2] = np.array([38, 40, 48], np.float32)
        hueco_arco = arco & ~intrados & ~intrados2
        # pilastras (cilindros) a los lados del arco
        for s in (-1, 1):
            cx = ax + s * (aw + 0.034 * W)
            r = 0.012 * W
            pil = (np.abs(xx - cx) < r) & (yy > atop - aw * 0.4) & (yy < suelo * H) & muro
            u = np.clip((xx - cx) / r, -1, 1)
            k = np.clip(0.55 - 0.6 * u, 0.2, 1.2)
            alb[pil] = (np.array([128, 132, 140], np.float32) * k[pil][:, None]) * (0.85 + 0.25 * ruido[pil])[:, None]
            cap = pil & (np.abs(yy - (atop - aw * 0.4)) < 2)
            alb[cap] = (170, 174, 176)
        # ventanas en arco (oscuras) con alféizar claro; la de la torre deja ver el cielo
        ven_cielo = np.zeros((H, W), bool)
        for vx, vy, vw, cielo in ((0.535, 0.37, 0.020, True), (0.745, 0.55, 0.014, False), (0.875, 0.24, 0.013, True),
                                  (0.875, 0.48, 0.011, False), (0.30, 0.62, 0.010, False)):
            v = dentro_arco(vx * W, vw * W, vy * H) & (yy < vy * H + vw * W * 3.0)
            v &= todo
            if cielo:
                ven_cielo |= v
            else:
                alb[v] = (12, 14, 20)
            sill = (np.abs(xx - vx * W) < vw * W + 1) & (np.abs(yy - (vy * H + vw * W * 3.0)) < 1) & todo
            alb[sill] = (150, 154, 156)
            marco = dentro_arco(vx * W, vw * W, vy * H, 1.5) & ~v & todo & (yy < vy * H + vw * W * 3)
            alb[marco] *= 1.35
        # musgo: sobre las caras de arriba de los bloques expuestos y enredaderas colgando
        ar, ab, iz, de = bordes(ids)
        expuesto = todo & (np.roll(~todo, 1, 0) | np.roll(hueco[ids] & todo, 1, 0))
        musgo = expuesto & (vnoise(W, H, 2, 170 + self.seed) > 0.5)
        mancha = todo & (fbm(W, H, 171 + self.seed, (10, 5, 2)) > 0.72) & (yy < 0.6 * H)
        mm = musgo | mancha
        verde = np.array([62, 92, 46], np.float32) * (0.7 + 0.6 * vnoise(W, H, 1, 173 + self.seed))[..., None]
        alb[mm] = alb[mm] * 0.25 + verde[mm] * vol[mm] * 1.1
        alb[mm & np.roll(~mm, 1, 0)] *= 1.3
        img = Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8))
        dr = ImageDraw.Draw(img)
        mk = Image.fromarray(((todo & ~hueco_arco & ~ven_cielo) * 255).astype(np.uint8))
        dm = ImageDraw.Draw(mk)
        for _ in range(14):                                      # enredaderas
            x0 = rng.uniform(0.40, 0.94) * W
            col = np.where(todo[:, int(min(x0, W - 1))])[0]
            if len(col) == 0:
                continue
            y0 = col[0] + rng.integers(0, 4)
            L = rng.uniform(0.03, 0.12) * H
            pts = [(x0 + math.sin(k * 0.8 + x0) * 1.2, y0 + L * k / 8) for k in range(9)]
            dr.line(pts, fill=(40, 62, 34), width=1)
            for k in range(1, 9, 2):
                dr.point(pts[k], fill=(96, 128, 60))

        # ================================================================ escalones
        for k in range(4):
            y0 = suelo * H - k * 0.013 * H
            w = aw * (1.35 - k * 0.07)
            y1 = y0 - 0.013 * H
            dr.rectangle([ax - w, y1, ax + w, y0], fill=(86, 90, 98))
            dr.line([(ax - w, y1), (ax + w, y1)], fill=(176, 182, 180))
            dr.line([(ax - w, y0), (ax + w, y0)], fill=(30, 32, 38))
            for j in range(6):
                jx = ax - w + (j + (k % 2) * 0.5) * (2 * w / 6)
                dr.line([(jx, y1), (jx, y0)], fill=(54, 56, 62))
            dm.rectangle([ax - w, y1, ax + w, y0], fill=255)
        alb = np.asarray(img, np.float32).copy()
        a = np.asarray(mk) > 0

        # ================================================================ suelo y camino
        suelo_m = yy >= suelo * H - 1
        tierra = np.array([62, 56, 46], np.float32) * (0.7 + 0.6 * fbm(W, H, 180 + self.seed, (16, 8, 4, 2)))[..., None]
        camino = np.exp(-(((xx - 0.52 * W) / (0.30 * W)) ** 2 + ((yy - 0.93 * H) / (0.11 * H)) ** 2))
        claro = np.array([1.0, 0.95, 0.80], np.float32)
        tierra = tierra * (0.55 + 1.9 * camino)[..., None] * claro
        alb[suelo_m] = tierra[suelo_m]
        a |= suelo_m
        # piedritas con luz y sombra
        img = Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8))
        dr = ImageDraw.Draw(img)
        for _ in range(55):
            x, y = rng.uniform(0.05, 0.95) * W, rng.uniform(0.82, 1.0) * H
            r = rng.uniform(0.003, 0.012) * S * (0.5 + (y / H - 0.8) * 3)
            c = 1.0 + 1.5 * float(np.exp(-(((x - 0.52 * W) / (0.3 * W)) ** 2 + ((y - 0.93 * H) / (0.11 * H)) ** 2)))
            dr.ellipse([x - r, y - r * 0.55, x + r, y + r * 0.55], fill=tuple(int(v * c) for v in (40, 40, 46)))
            dr.point((x - r * 0.4, y - r * 0.3), fill=tuple(int(min(255, v * c)) for v in (84, 84, 82)))
        for _ in range(140):                                     # pasto seco en matas
            x, y = rng.uniform(0, W), rng.uniform(0.79, 0.99) * H
            c = 1.0 + 1.2 * float(np.exp(-(((x - 0.52 * W) / (0.3 * W)) ** 2 + ((y - 0.93 * H) / (0.11 * H)) ** 2)))
            for j in range(3):
                h = rng.uniform(2, 6) * (0.6 + (y / H - 0.78) * 3)
                dr.line([(x + j, y), (x + j + rng.uniform(-2, 2), y - h)],
                        fill=tuple(int(min(255, v * c)) for v in ((110, 92, 58) if j % 2 else (84, 70, 46))))
        alb = np.asarray(img, np.float32).copy()

        # ================================================================ rocas con volumen
        def roca(cx, cy, r, sem, base=(74, 78, 88)):
            nonlocal alb, a
            rr = np.random.default_rng(sem)
            n = 8
            pts = [(cx + math.cos(k / n * 2 * math.pi) * r * rr.uniform(0.7, 1.15),
                    cy + math.sin(k / n * 2 * math.pi) * r * 0.62 * rr.uniform(0.7, 1.15)) for k in range(n)]
            rm = self.m(lambda d: d.polygon(pts, fill=255))
            if not rm.any():
                return
            sombra = self.m(lambda d: d.ellipse([cx - r * 1.1, cy + r * 0.2, cx + r * 1.3, cy + r * 0.75], fill=255)) & ~rm
            alb[sombra] *= 0.55
            facetas = (vnoise(W, H, max(2, int(r / 2)), sem) - 0.5) * r * 0.5
            col = sombrear(rm, base, LUZ, radio=max(1.5, r * 0.35), relieve=r * 0.7, ruido=facetas, ambiente=0.3,
                           brillo=0.15)
            grieta = rm & (np.abs(fbm(W, H, sem + 1, (max(3, int(r)), max(2, int(r / 2)))) - 0.5) < 0.012)
            col[grieta] *= 0.5
            arriba = rm & np.roll(~rm, 2, 0) & (vnoise(W, H, 2, sem + 2) > 0.55)
            col[arriba] = col[arriba] * 0.4 + np.array([70, 100, 50], np.float32) * 0.6
            alb[rm] = col[rm]
            a |= rm

        for k in range(22):                                      # escombros al pie de las ruinas
            side = [0.27, 0.62, 0.78][k % 3]
            roca(rng.uniform(side - 0.10, side + 0.12) * W, rng.uniform(0.75, 0.84) * H, rng.uniform(0.018, 0.045) * S, 200 + k)
        for k, (fx, fy, fr) in enumerate(((0.24, 0.84, 0.07), (0.72, 0.90, 0.065), (0.98, 0.86, 0.06), (0.40, 0.99, 0.05))):
            roca(fx * W, fy * H, fr * S, 300 + k)

        # ================================================================ matorrales rojizos
        for fx, fy, fr, sem in ((0.03, 0.70, 0.09, 1), (0.97, 0.64, 0.08, 2)):
            bm = np.zeros((H, W), bool)
            for _ in range(26):
                x, y = fx * W + rng.uniform(-fr, fr) * S, fy * H + rng.uniform(-fr, fr) * S * 0.9
                r = rng.uniform(0.012, 0.03) * S
                bm |= (xx - x) ** 2 + (yy - y) ** 2 < r * r
            hojas = (vnoise(W, H, 1, 400 + sem) - 0.5) * 3
            col = sombrear(bm, (96, 44, 46), LUZ, radio=0.02 * S, relieve=0.04 * S, ruido=hojas, ambiente=0.25, brillo=0)
            alb[bm] = col[bm]
            a |= bm

        # ================================================================ árbol seco
        if p.get("arbol", True):
            img = Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8))
            dr = ImageDraw.Draw(img)
            ramas_m = Image.new("L", (W, H), 0)
            drm = ImageDraw.Draw(ramas_m)

            def rama(x, y, ang, largo, grosor, nivel):
                x2 = x + math.cos(ang) * largo
                y2 = y + math.sin(ang) * largo
                n = max(2, int(largo / 1.5))
                for k in range(n):                                # rama cónica (se adelgaza)
                    u = k / n
                    g = grosor * (1 - 0.45 * u)
                    px, py = x + (x2 - x) * u + math.sin(u * 6 + nivel) * 0.6, y + (y2 - y) * u
                    drm.ellipse([px - g / 2, py - g / 2, px + g / 2, py + g / 2], fill=255)
                if nivel <= 0 or largo < 2.5:
                    return
                for da in (rng.uniform(-0.85, -0.3), rng.uniform(0.25, 0.75)):
                    rama(x2, y2, ang + da, largo * rng.uniform(0.62, 0.8), grosor * 0.55, nivel - 1)

            tx, ty = 0.13 * W, suelo * H + 1
            drm.polygon([(tx - 0.045 * S, ty), (tx + 0.04 * S, ty), (tx + 0.016 * S, ty - 0.18 * H), (tx - 0.014 * S, ty - 0.18 * H)], fill=255)
            for rx in (-0.07, 0.07):                              # raíces
                drm.polygon([(tx, ty - 0.02 * H), (tx + rx * S, ty + 1), (tx + rx * S * 0.4, ty + 1)], fill=255)
            rama(tx + 0.001 * W, ty - 0.18 * H, -1.35, 0.13 * H, 0.03 * S, 5)
            rama(tx - 0.004 * W, ty - 0.15 * H, -2.45, 0.10 * H, 0.024 * S, 4)
            rama(tx + 0.008 * W, ty - 0.12 * H, -0.42, 0.12 * H, 0.022 * S, 4)
            tm = np.asarray(ramas_m) > 127
            corteza = (np.repeat(vnoise(W // 2 + 1, H, 3, 410), 2, axis=1)[:, :W] - 0.5) * 1.5
            col = sombrear(tm, (92, 66, 52), LUZ, radio=0.012 * S, relieve=0.025 * S, ruido=corteza, ambiente=0.3, brillo=0.05)
            alb = np.asarray(img, np.float32).copy()
            alb[tm] = col[tm]
            a |= tm

        self.mid_alb, self.mid_a = alb, a
        if p.get("antorchas"):
            for s in (-1, 1):
                antorcha(self, ax + s * (aw + 0.05 * W), 0.62 * H, tam=0.03 * S, radio=0.12 * S, intensidad=0.9)

        # ================================================================ primer plano: rocas oscuras en las esquinas
        fg = np.zeros((H, W), bool)
        for cx, cy, r in ((0.02, 1.02, 0.16), (0.16, 1.04, 0.09), (0.92, 1.03, 0.15), (0.78, 1.05, 0.08)):
            fg |= self.m(lambda d, cx=cx, cy=cy, r=r: d.polygon(
                [(cx * W + math.cos(k / 7 * 2 * math.pi) * r * S * rng.uniform(0.8, 1.1),
                  cy * H + math.sin(k / 7 * 2 * math.pi) * r * S * 0.6) for k in range(7)], fill=255))
        self.fg_a = fg
        self.fg_alb = sombrear(fg, (70, 74, 84), LUZ, radio=0.03 * S, relieve=0.08 * S,
                               ruido=(vnoise(W, H, 4, 420) - 0.5) * 4, ambiente=0.35, brillo=0.1)

        self.lights.append(Light("luna", self.point(mx, my, 1.2 * S, 0.40), (0.75, 0.84, 0.92)))
        self.lights.append(Light("camino", self.pool(0.52 * W, 0.93 * H, 0.33 * W, 0.09 * H, 0.30), (0.95, 0.9, 0.75)))
