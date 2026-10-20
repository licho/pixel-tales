"""Muralla de frontera romana (estilo Muro de Adriano) de noche, con niebla y antorchas.

El adarve (pasillo de arriba) se aleja hacia el fondo; a la izquierda el parapeto con almenas,
a la derecha el vacío con colinas y niebla.

Parámetros:
  antorchas  int  cuántas antorchas en el parapeto (default 4)
  niebla     0-1  (default 0.6)
  luna       bool (default true)
  semilla    int

Puntos útiles (vertical 256x384): punto de fuga (0.58 W, 0.40 H).
  Legionarios sobre el adarve: cerca (0.45 W, 0.93 H, escala 1.6), medio (0.52 W, 0.62 H, escala 0.8),
  lejos (0.56 W, 0.50 H, escala 0.4). El adarve en una y dada va de x_izq(y) a x_der(y): ver geometria().
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth
from pixel_tales.pintura import antorcha, estrellas, piedra_bloques
from pixel_tales.scene import Scene


class Escena(Scene):
    formatos = ("horizontal", "vertical")
    parallax = {"sky": 0.08, "far": 0.2, "mid": 0.6, "fg": 1.2}

    def geometria(self, y):
        """x izquierda/derecha del adarve a la altura y (perspectiva lineal hacia el punto de fuga)."""
        W, H = self.W, self.H
        fx, fy = 0.58 * W, 0.40 * H
        v = np.clip((y - fy) / (H - fy), 0, 1)
        return fx + (-0.25 * W - fx) * v, fx + (0.95 * W - fx) * v

    def build(self):
        W, H = self.W, self.H
        p = self.p
        xx, yy = self.grid()
        rng = np.random.default_rng(90 + self.seed)
        fx, fy = 0.58 * W, 0.40 * H

        t = np.clip(yy / (0.5 * H), 0, 1)[..., None]
        sky = np.array([8, 8, 16], np.float32) * (1 - t) + np.array([34, 34, 52], np.float32) * t
        estrellas(self, sky, 0.003, 0.35, self.seed, (190, 190, 210))
        if p.get("luna", True):
            lx, ly = 0.25 * W, 0.12 * H
            dd = np.hypot(xx - lx, yy - ly)
            sky += (np.exp(-dd / (0.12 * W)) * 40)[..., None] * np.array([0.7, 0.75, 1.0], np.float32)
            sky[dd < 9] = (210, 210, 220)
            sky[(dd < 9) & (np.hypot(xx - lx - 3, yy - ly + 2) < 7)] = (176, 178, 180)
        self.sky = sky

        # colinas lejanas (derecha)
        far = Image.new("L", (W, H), 0)
        fd = ImageDraw.Draw(far)
        for layer, (base, amp) in enumerate(((0.43, 0.05), (0.50, 0.06))):
            pts = [(-5, H)]
            for x in np.linspace(-5, W + 5, 30):
                pts.append((x, base * H - amp * H * (0.5 + 0.5 * np.sin(x * 0.04 + layer * 3 + self.seed))))
            pts.append((W + 5, H))
            fd.polygon(pts, fill=100 + layer * 100)
        fa = np.asarray(far)
        self.far_a = fa > 0
        self.far = np.where((fa > 150)[..., None], np.array([26, 30, 40], np.float32), np.array([40, 44, 60], np.float32)) * np.ones((H, W, 1), np.float32)

        # muro: cara exterior (derecha) que baja, adarve, parapeto izquierdo con almenas
        piedra = piedra_bloques(self, (92, 88, 84), 10, 5, self.seed)
        piso = piedra_bloques(self, (84, 78, 70), 16, 4, self.seed + 3)
        img = Image.new("RGB", (W, H))
        mk = Image.new("L", (W, H), 0)
        d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mk)

        arr = np.zeros((H, W, 3), np.float32)
        xl, xr = self.geometria(yy)
        on_floor = (yy >= fy) & (xx >= xl) & (xx <= xr)
        v = np.clip((yy - fy) / (H - fy), 0, 1)
        arr[on_floor] = piso[on_floor] * (0.55 + 0.45 * v[on_floor])[..., None]
        # cara exterior del muro (debajo del borde derecho del adarve)
        cara_h = 0.05 * H + 0.35 * H * v
        cara = (yy >= fy) & (xx > xr) & (xx < xr + 3 + 6 * v) | ((xx >= xr) & (yy >= fy) & (yy < fy + 2))
        edge_y = fy + (xx - fx) / (0.95 * W - fx) * (H - fy)
        cara = (xx > fx) & (yy > edge_y) & (yy < edge_y + 0.03 * H + 0.3 * H * np.clip((xx - fx) / (0.37 * W), 0, 1))
        arr[cara] = piedra[cara] * 0.45
        floor_a = on_floor | cara

        # parapeto izquierdo: banda vertical que crece hacia la cámara, con almenas
        par = np.zeros((H, W), bool)
        pz = np.zeros((H, W), bool)
        n = 26
        for k in range(n):
            v0, v1 = (k / n) ** 1.6, ((k + 1) / n) ** 1.6
            ya, yb = fy + v0 * (H - fy), fy + v1 * (H - fy)
            xa, _ = self.geometria(ya)
            xb, _ = self.geometria(yb)
            alto_a, alto_b = 4 + 0.30 * H * v0, 4 + 0.30 * H * v1
            poly = [(xa, ya), (xb, yb), (xb, yb - alto_b), (xa, ya - alto_a)]
            m = self.mask(lambda dd, poly=poly: dd.polygon(poly, fill=255))
            par |= m
            if k % 2 == 0:                               # almena (merlón)
                ex = (alto_a + alto_b) * 0.22
                poly2 = [(xa, ya - alto_a), (xb, yb - alto_b), (xb, yb - alto_b - ex), (xa, ya - alto_a - ex)]
                m2 = self.mask(lambda dd, poly2=poly2: dd.polygon(poly2, fill=255))
                pz |= m2
        par_all = par | pz
        arr[par_all] = piedra[par_all] * 0.7
        # sombra: el parapeto es más oscuro abajo
        self.mid_alb = arr
        self.mid_a = floor_a | par_all
        self.mid_alb[pz] *= 1.08

        # antorchas en el parapeto (de lejos a cerca)
        na = int(p.get("antorchas", 4))
        for k in range(na):
            vv = (0.12 + 0.8 * k / max(na - 1, 1)) ** 1.5
            y = fy + vv * (H - fy)
            x, _ = self.geometria(y)
            alto = 4 + 0.30 * H * vv
            x += 6 + 20 * vv
            if x < 4:
                continue
            antorcha(self, x, y - alto * 0.55, tam=0.5 + 1.4 * vv, radio=30 + 30 * vv, intensidad=1.0, contraluz=True)

        # niebla: más densa a la derecha (vacío) y al fondo
        nb = float(p.get("niebla", 0.6))
        nf = fbm(W, H, 95 + self.seed, (48, 24, 12))
        fogc = np.array([70, 76, 96], np.float32)
        kk = (np.exp(-((yy - fy) / (0.12 * H)) ** 2) * 0.7 + 0.35 * smooth(0.45, 0.75, nf)) * nb
        self.mid_alb = self.mid_alb * (1 - kk[..., None]) + fogc * kk[..., None]
        self.far = self.far * (1 - 0.6 * nb) + fogc * 0.6 * nb
        self.fog_k = kk
        self.nf = nf

        self.lights.append(Light("luna", self.point(0.25 * W, 0, 1.3 * H, 0.35), (0.55, 0.62, 0.9)))
