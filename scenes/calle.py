"""Calle urbana abandonada en perspectiva de un punto, de noche.

Parámetros:
  semilla  (int)   varía nubes y texturas
  farol    (bool)  farol con charco de luz y haz volumétrico (default true)
  barril   (bool)  barril con fuego a la izquierda (default true)
  carro    (bool)  carro abandonado a la derecha (default true)
  cables   (bool)  poste y cables de luz (default true)

Puntos útiles para actores (x, y = pies):
  banqueta izquierda: x 60-130, y 195-212 (el sobreviviente queda bien en [96, 208])
  calle a media distancia: [200-320, 140-170]   (zombis de altura 10-30)
"""
import numpy as np

from pixel_tales.core import LW, LH, Light, fbm, grid, mask, point_light, pool_light, smooth, vnoise
from pixel_tales.scene import Scene

VP = (230, 120)  # punto de fuga


class Escena(Scene):
    formatos = ("horizontal",)

    def build(self):
        p = self.p
        self.xx, self.yy = grid()
        self._sky()
        self._far()
        self._street(p.get("farol", True), p.get("barril", True), p.get("carro", True), p.get("cables", True))
        self._fg()

    # ------------------------------------------------------------ cielo ---
    def _sky(self):
        xx, yy = self.xx, self.yy
        t = np.clip(yy / 125, 0, 1)[..., None]
        col = np.array([12, 22, 26.]) * (1 - t) + np.array([46, 72, 72.]) * t
        n = fbm(LW, LH, 10 + self.seed, (64, 32, 16, 8))
        cloud = smooth(0.48, 0.72, n)
        under = cloud[np.clip(np.arange(LH) - 3, 0, LH - 1)]
        col = col * (1 - 0.35 * cloud[..., None]) + np.array([66, 96, 92.]) * (cloud * 0.55)[..., None]
        col -= (np.clip(under - cloud, 0, 1) * 18)[..., None]
        d = np.hypot(xx - 118, yy - 26)
        col += (np.exp(-d / 26) * 40)[..., None] * np.array([0.8, 1, 0.95])
        col = np.where((d < 7)[..., None], np.array([170, 186, 176.]) * (1 - 0.4 * cloud[..., None]), col)
        for bx, by in [(268, 34), (276, 30), (284, 36), (296, 28), (262, 26)]:
            col[by, bx - 1] = col[by, bx + 1] = (14, 20, 22)
            col[by - 1, bx - 2] = col[by - 1, bx + 2] = (14, 20, 22)
        self.sky = col

    # ----------------------------------------------------- rascacielos ---
    def _far(self):
        rng = np.random.default_rng(9)
        alb = np.zeros((LH, LW, 3), np.float32)
        em = np.zeros((LH, LW, 3), np.float32)
        a = np.zeros((LH, LW), bool)
        towers = [(150, 70, 30), (178, 46, 22), (198, 22, 26), (222, 58, 18), (238, 34, 30),
                  (266, 10, 16), (280, 50, 26), (304, 30, 24), (326, 66, 30), (350, 84, 28)]
        for x0, top, w in towers:
            a[top:126, x0:x0 + w] = True
            alb[top:126, x0:x0 + w] = (30, 46, 48) if rng.random() < 0.5 else (26, 40, 44)
            alb[top:126, x0:x0 + 2] = (40, 58, 60)
            for wy in range(top + 4, 120, 4):
                for wx in range(x0 + 3, x0 + w - 2, 3):
                    if rng.random() < 0.022:
                        em[wy, wx] = (170, 92, 32)
        a[0:10, 273] = True
        alb[0:10, 273] = (30, 46, 48)
        a[4:10, 272:275] = True
        fog = smooth(60, 126, self.yy)[..., None]
        self.far = alb * (1 - 0.65 * fog) + np.array([58, 86, 86.]) * 0.65 * fog + em * (1 - fog)
        self.far_a = a

    # ------------------------------------------------------------ calle ---
    def _street(self, farol, barril, carro, cables):
        xx, yy = self.xx, self.yy
        alb, a, em = self.mid_alb, self.mid_a, self.mid_em
        grain = vnoise(LW, LH, 2, 21 + self.seed) - 0.5
        vx, vy = VP

        ground = yy >= vy - 1
        puddle = smooth(0.62, 0.68, fbm(LW, LH, 31 + self.seed, (24, 12, 6)))
        road = (np.array([96, 104, 104.]) + grain[..., None] * 18) * (1 - 0.35 * puddle[..., None])
        alb[ground] = road[ground]
        a |= ground

        left_sw = mask(lambda d: d.polygon([(0, 178), (170, 135), (170, 153.9), (60, 216), (0, 216)], fill=255))
        right_sw = mask(lambda d: d.polygon([(424, 196), (300, 147.4), (300, 164.8), (380, 216), (424, 216)], fill=255))
        sw = np.array([86, 92, 90.]) + grain[..., None] * 14
        alb[left_sw] = sw[left_sw]
        alb[right_sw] = sw[right_sw]
        curb = mask(lambda d: (d.line([(170, 153.9), (60, 216)], fill=255, width=2),
                               d.line([(300, 164.8), (380, 216)], fill=255, width=2)))
        alb[curb] = (128, 132, 128)

        for k in range(1, 30):  # línea central discontinua
            z0, z1 = 1 + k * 0.55, 1 + k * 0.55 + 0.28
            y0, y1 = vy + 96 / z1, vy + 96 / z0
            if y1 - y0 < 0.6:
                continue
            x0, x1 = vx + 20 / z1, vx + 20 / z0
            seg = mask(lambda d: d.line([(x0, y0), (x1, y1)], fill=255, width=max(1, int(3 / z0))))
            alb[seg] = (150, 146, 118)

        self._facade_left(grain)
        self._facade_right(grain)

        if cables:
            pole = mask(lambda d: (d.line([(140, 158), (140, 44)], fill=255, width=3),
                                   d.line([(130, 50), (150, 50)], fill=255, width=2)))
            alb[pole] = (44, 38, 32)
            a |= pole

            def wires(d):
                for x0, y0, x1, y1, sag in [(140, 50, 424, 30, 26), (140, 50, 424, 44, 30),
                                            (140, 54, 0, 30, 14), (140, 54, 0, 42, 10)]:
                    pts = [(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + sag * 4 * u * (1 - u))
                           for u in np.linspace(0, 1, 41)]
                    d.line(pts, fill=255, width=1)
            wm = mask(wires)
            alb[wm] = (16, 20, 22)
            a |= wm

        if farol:
            lamp = mask(lambda d: (d.line([(332, 176), (332, 82)], fill=255, width=3),
                                   d.line([(332, 82), (308, 80)], fill=255, width=2),
                                   d.rectangle([302, 79, 312, 83], fill=255)))
            alb[lamp] = (30, 38, 40)
            a |= lamp
            em[82:84, 303:311] = (255, 240, 200)
            t = np.clip((yy - 84) / 106, 0, 1)
            cone = ((np.abs(xx - (307 - 18 * t)) < 6 + 52 * t) * (yy > 84) * (1 - t) ** 1.4).astype(np.float32)
            self.lights.append(Light("farol", pool_light(286, 182, 74, 24, 1.35, 118) + point_light(307, 86, 55, 0.55),
                                     (0.92, 1.0, 0.95), parpadeo="farol",
                                     volumen=cone[..., None] * np.array([30, 38, 36], np.float32)))

        if carro:
            body = [(326, 202), (332, 190), (348, 183), (362, 176), (398, 175), (412, 184), (418, 194), (418, 206), (326, 206)]
            out = mask(lambda d: d.polygon([(x + (1 if x > 370 else -1), y + (1 if y > 190 else -1)) for x, y in body], fill=255))
            car = mask(lambda d: d.polygon(body, fill=255))
            alb[out] = (18, 22, 24)
            alb[car] = np.array([150, 144, 128.]) + grain[car][..., None] * 10
            alb[car & (yy > 197)] = (110, 104, 92)
            cw = mask(lambda d: d.polygon([(350, 186), (364, 179), (396, 178), (406, 186)], fill=255))
            alb[cw] = (34, 46, 50)
            alb[cw & (np.abs(xx - 380 - (yy - 182) * 1.5) < 1)] = (146, 166, 156)
            alb[195:199, 327:331] = (60, 26, 24)
            wh = mask(lambda d: (d.ellipse([336, 199, 350, 212], fill=255), d.ellipse([396, 199, 410, 212], fill=255)))
            alb[wh] = (14, 18, 20)
            a |= car | wh | out

        if barril:
            b = mask(lambda d: d.rectangle([44, 178, 60, 198], fill=255))
            alb[b] = (102, 40, 34)
            alb[b & ((yy.astype(int) - 178) % 7 < 1)] = (60, 26, 24)
            alb[b & (xx < 47)] *= 0.6
            a |= b
            self.fires.append({"x0": 45, "x1": 60, "y": 177, "humo": True})
            self.lights.append(Light("barril", point_light(52, 176, 42, 1.15), (1.0, 0.55, 0.22),
                                     parpadeo="fuego", contraluz=True))

        rng = np.random.default_rng(3)
        for _ in range(40):  # papeles
            px, py = int(rng.integers(0, 200)), int(rng.integers(180, 215))
            if left_sw[py, px] or py > 205:
                alb[py, px:px + 2] = (150, 146, 130)

    def _facade_left(self, grain):
        xx, yy = self.xx, self.yy
        vx, vy = VP
        top = vy + (-10 - vy) * (vx - xx) / vx
        bot = vy + (178 - vy) * (vx - xx) / vx
        m = (xx < 170) & (yy >= top) & (yy <= bot)
        z = vx / np.maximum(vx - xx, 1)
        v = (yy - top) / np.maximum(bot - top, 1)
        bay = (z - 1) / 0.38
        bi, bf = np.floor(bay), bay % 1
        fv = (v - 0.07) / 0.17
        ri, rf = np.floor(fv), fv % 1
        col = np.array([80, 58, 46.]) + grain[..., None] * 16
        col[bf < 0.07] *= 0.7
        col[v < 0.03] = (100, 80, 62)
        win = (bf > 0.24) & (bf < 0.76) & (rf > 0.18) & (rf < 0.78) & (ri >= 0) & (ri <= 3)
        h = (bi * 7.3 + ri * 3.1) % 1
        glass = np.array([22, 30, 32.]) + 30 * (rf < 0.32)[..., None] * (bf < 0.45)[..., None]
        col = np.where(win[..., None], glass, col)
        lit = win & (h > 0.86) & (xx > 128)
        col[win & (h < 0.22) & ((bf * 13 + rf * 7) % 1 < 0.5)] = (8, 12, 13)
        store = v > 0.76
        col[store] = (26, 24, 22)
        posters = store & (z > 1.5) & (bf > 0.15) & (bf < 0.85) & (v > 0.81) & (v < 0.91)
        ph = (np.floor(bf * 6) * 3.7 + np.floor(v * 20) * 1.3) % 1
        col[posters & (ph > 0.35)] = (168, 158, 136)
        col[posters & (ph > 0.8)] = (150, 56, 44)
        self.mid_alb[m] = col[m]
        self.mid_a |= m
        self.mid_em[lit & m] = (200, 120, 40)

    def _facade_right(self, grain):
        xx, yy = self.xx, self.yy
        vx, vy = VP
        top = vy + (-20 - vy) * (xx - vx) / 194
        bot = vy + (196 - vy) * (xx - vx) / 194
        m = (xx >= 300) & (yy >= top) & (yy <= bot)
        z = 194 / np.maximum(xx - vx, 1)
        v = (yy - top) / np.maximum(bot - top, 1)
        bay = (z - 1) / 0.42
        bi, bf = np.floor(bay), bay % 1
        fv = (v - 0.06) / 0.16
        ri, rf = np.floor(fv), fv % 1
        col = np.array([78, 96, 100.]) + grain[..., None] * 14
        col[bf < 0.06] *= 0.75
        win = (bf > 0.22) & (bf < 0.78) & (rf > 0.2) & (rf < 0.8) & (ri >= 0) & (ri <= 3)
        h = (bi * 5.7 + ri * 2.3) % 1
        lx, ly = (bf - 0.22) / 0.56, (rf - 0.2) / 0.6
        board = win & (h > 0.45)
        plank = board & ((np.abs(lx - ly) < 0.16) | (np.abs(lx + ly - 1) < 0.16) | (ly < 0.12) | (ly > 0.88))
        col = np.where(win[..., None], np.array([24, 32, 34.]), col)
        col[board] = (40, 30, 24)
        col[plank] = (176, 96, 40)
        store = v > 0.78
        col[store] = np.array([60, 70, 72.]) * (0.75 + 0.25 * ((yy.astype(int) % 2) == 0))[store][..., None]
        self.mid_alb[m] = col[m]
        self.mid_a |= m

    # --------------------------------------------------------- primer plano
    def _fg(self):
        rng = np.random.default_rng(8 + self.seed)
        for x in range(0, LW, 2):
            hgt = int(4 + 6 * abs(np.sin(x * 0.13)) + rng.integers(0, 4))
            self.fg_a[LH - hgt:, x:x + 2] = True
            self.fg_alb[LH - hgt:, x:x + 2] = (14, 20, 22)
            if rng.random() < 0.3:
                self.fg_alb[LH - hgt, x] = (36, 52, 44)
