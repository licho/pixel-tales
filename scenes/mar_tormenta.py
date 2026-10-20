"""Mar abierto en tormenta: nubes pesadas, cortinas de lluvia, olas animadas con espuma, niebla
y rayo (con el efecto `relampago`). También sirve para mar en calma (olas bajas) o noche en altamar.

Parámetros:
  horizonte  0-1 de la altura (default 0.60 horizontal, 0.62 vertical)
  olas       fuerza del oleaje, 0.2 (calma) a 1.5 (tormenta fuerte)   (default 1.0)
  claro      [x, y] relativos: hueco luminoso entre las nubes (y origen del rayo) (default [0.86, 0.30])
  niebla     bool (default true)
  espuma     lista de zonas de salpicadura [x, y, ancho] relativos (ej. donde algo sale del agua)
  semilla    int

Las olas tapan a los actores según su profundidad: un actor con pies en `y` queda detrás de las olas
más cercanas a la cámara. Para un barco usa un sprite con `flota` y `balanceo`.

Puntos útiles (relativos a W x H; pies = línea del agua):
  barco cercano: (0.35 W, 0.86 H) ; criatura saliendo del mar: (0.5 W, 0.78 H)
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.scene import Scene

TAU = 2 * math.pi


def ruido_1d(n, puntos, rng):
    """Ruido suave periódico de longitud n."""
    xs = np.linspace(0, n, puntos + 1)
    v = rng.random(puntos + 1)
    v[-1] = v[0]
    return np.interp(np.arange(n), xs, v)


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.1, "far": 0.3, "mid": 0.6, "fg": 1.0}

    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        rng = np.random.default_rng(50 + self.seed)
        self.hy = hy = float(p.get("horizonte", 0.62 if H > W else 0.60)) * H
        olas = float(p.get("olas", 1.0))
        cx, cy = p.get("claro", [0.86, 0.30])
        cx, cy = cx * W, cy * H

        # ---------------- cielo: nubes pesadas, claro luminoso, cortinas de lluvia
        t = np.clip(yy / hy, 0, 1)[..., None]
        sky = np.array([16, 20, 24], np.float32) * (1 - t) + np.array([66, 76, 82], np.float32) * t
        n = fbm(W, H, 11 + self.seed, (64, 32, 16, 8))
        n2 = fbm(W, H, 17 + self.seed, (24, 12, 6))
        dark = smooth(0.45, 0.65, n)
        sky = sky * (1 - 0.55 * dark[..., None]) + np.array([14, 17, 20], np.float32) * 0.55 * dark[..., None]
        edge = np.clip(1 - np.abs(n - 0.47) / 0.08, 0, 1) * smooth(0.4, 0.7, n2)          # bordes de nube iluminados
        g = np.exp(-(((xx - cx) / (0.30 * W)) ** 2 + ((yy - cy) / (0.20 * H)) ** 2))
        sky += (g * (1 - dark) * 80)[..., None] * np.array([0.9, 0.95, 1.0])
        sky += (edge * (14 + 60 * g))[..., None] * np.array([0.9, 0.95, 1.0])
        shafts = np.asarray(Image.fromarray((vnoise(W, 6, 5, 3 + self.seed) * 255).astype(np.uint8))
                            .resize((W, H), Image.BILINEAR), np.float32) / 255
        rows = np.arange(H)
        shafts = shafts[rows[:, None], (np.arange(W)[None, :] + (rows[:, None] * 0.3).astype(int)) % W]
        sky *= (1 - 0.12 * smooth(0.5, 0.8, shafts))[..., None]
        sky = np.minimum(sky, 235)
        self.sky = sky

        # rayo (para el efecto relampago)
        flash = np.minimum(sky * 1.35 + 16, 175)
        bolt = Image.new("L", (W, H), 0)
        bd = ImageDraw.Draw(bolt)
        x, y = cx, cy - 0.10 * H
        pts = [(x, y)]
        while y < hy - 0.08 * H:
            x += rng.uniform(-0.035, 0.015) * W
            y += rng.uniform(0.025, 0.05) * H
            pts.append((x, y))
            if rng.random() < 0.35:
                bx, by = x, y
                for _ in range(3):
                    nx_, ny_ = bx + rng.uniform(0.0, 0.03) * W, by + rng.uniform(0.01, 0.03) * H
                    bd.line([(bx, by), (nx_, ny_)], fill=160, width=1)
                    bx, by = nx_, ny_
        bd.line(pts, fill=255, width=max(2, int(W / 200)))
        b = np.asarray(bolt, np.float32) / 255
        glow = np.asarray(bolt.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(4)), np.float32) / 255
        flash = flash + (glow * 90)[..., None] * np.array([0.85, 0.85, 1.0])
        flash = np.where((b > 0.3)[..., None], np.array([240, 236, 255], np.float32), flash)
        self.sky_flash = np.minimum(flash, 245)

        # ---------------- mar: filas de olas de atrás hacia adelante (se pintan en animar)
        k = (H - hy) / (216 * 0.4)
        self.rows = []
        nrows = 18
        for i in range(nrows):
            u = (i + 1) / nrows
            base = hy + (H * 1.10 - hy) * u ** 1.5
            amp = (0.5 + 30 * u ** 1.9) * olas * k
            lam = (9 + 150 * u ** 1.3) * k
            self.rows.append(dict(
                u=u, base=base, amp=amp, lam=lam, w=0.7 + 1.1 * (1 - u) + rng.uniform(-0.2, 0.2),
                ph=rng.uniform(0, TAU), ph2=rng.uniform(0, TAU), nz=ruido_1d(W, max(4, int(W / (lam * 0.6))), rng)))
        self.N = vnoise(W, H, 2, 70 + self.seed)
        self.S = np.repeat(vnoise(W, H // 3 + 1, 4, 71 + self.seed), 3, axis=0)[:H]   # vetas de espuma
        self.fog = fbm(W, H, 80 + self.seed, (48, 24, 12)) if p.get("niebla", True) else None
        self.zonas = [(z[0] * W, z[1] * H, z[2] * W) for z in p.get("espuma", [])]
        self.spray = []
        for zx, zy, zw in self.zonas:
            m = int(zw * 1.6)
            self.spray.append(np.column_stack([zx + rng.uniform(-0.5, 0.5, m) * zw, rng.uniform(0.7, 1.6, m),
                                               rng.uniform(0, 2, m), rng.uniform(0.04, 0.16, m) * H,
                                               rng.uniform(-6, 6, m)]))
        self.lights.append(Light("claro", self.point(cx, cy, 0.6 * W, 0.35), (0.8, 0.85, 0.95)))

    def animar(self, col, t):
        W, H = self.W, self.H
        xx, yy = self.grid()
        xs = np.arange(W)
        depth = getattr(self, "depth", None)
        if depth is None:
            depth = np.full((H, W), -1.0, np.float32)
        fl = 1.55 if getattr(self, "flash", False) else 1.0
        sea_a = np.zeros((H, W), bool)
        haze = np.array([66, 76, 82], np.float32)
        nrows = len(self.rows)
        for i, r in enumerate(self.rows):
            u, A, lam, w = r["u"], r["amp"], r["lam"], r["w"]
            env = np.interp((xs + t * 5 * w) % W, xs, r["nz"])               # olas grandes y chicas
            phase = TAU * xs / lam + w * t + r["ph"] + 2.2 * env                # deforma para que no se repitan
            sw = 0.5 + 0.5 * np.sin(phase)
            crest = sw ** 2.2
            chop = 0.5 + 0.5 * np.sin(TAU * xs / (lam * 0.37) - 1.7 * w * t + r["ph2"])
            h = A * (crest * (0.35 + 0.85 * env) + 0.12 * chop)
            top = r["base"] - h
            y0 = max(0, int(top.min()))
            y1 = H if i == nrows - 1 else min(H, int(self.rows[i + 1]["base"]) + 2)
            if y0 >= y1:
                continue
            Y = yy[y0:y1]
            dist = Y - top[None, :]
            m = (dist >= 0) & (depth[y0:y1] < r["base"])
            if not m.any():
                continue
            dpos = np.maximum(dist, 0)
            face = np.exp(-dpos / (A * 0.8 + 0.8))
            side = 0.5 + 0.5 * np.cos(phase)                                   # una cara de la ola recibe luz
            c = np.empty(Y.shape + (3,), np.float32)
            c[:] = np.array([12, 19, 26], np.float32) * (0.75 + 0.5 * u)
            c += (face * (0.25 + 0.75 * side[None, :]) * (0.4 + 0.9 * crest[None, :]))[..., None] \
                * np.array([52, 70, 78], np.float32)
            sh = int(t * 8 * w) % W
            idx = (xs + sh) % W
            Nn = self.N[y0:y1][:, idx]
            brk = crest * env                                                  # qué tanto rompe la ola
            core = (dpos < 1 + A * 0.22 * brk[None, :]) & (brk[None, :] > 0.5)
            spill = (Nn > 1 - 1.1 * np.clip(brk[None, :] - 0.3, 0, 1) * np.exp(-dpos / (A * 0.6 + 0.8)))
            drip = (self.S[y0:y1][:, idx] > 0.78) & (dpos < A * 0.5) & (brk[None, :] > 0.6) & ((xs[None, :] % 5) == 0)
            vet = (self.S[y0:y1][:, (xs + sh // 2) % W] > 0.74) & (dpos > A * 0.4)
            c[vet] = c[vet] * 0.65 + np.array([84, 98, 104], np.float32) * 0.35
            foam = core | spill | drip
            c[foam] = np.array([200, 208, 210], np.float32) * (0.7 + 0.3 * Nn[foam])[..., None]
            hz = (1 - u) ** 2.2
            c = c * (1 - hz) + haze * hz
            reg = col[y0:y1]
            reg[m] = (c * fl)[m]
            sea_a[y0:y1] |= m
        # salpicaduras donde algo sale del agua
        for zone, parts in zip(self.zonas, self.spray):
            zx, zy, zw = zone
            mist = np.exp(-(((xx - zx) / (zw * 0.6)) ** 2 + ((yy - zy + 0.05 * H) / (0.10 * H)) ** 2)) * 0.45
            mm = (sea_a | (depth >= 0)) & (mist > 0.02)
            col[mm] = col[mm] * (1 - mist[mm, None]) + np.array([150, 160, 166], np.float32) * fl * mist[mm, None]
            for x0, T, ph, hgt, dx in parts:
                tau = ((t + ph) % T) / T
                y = zy - hgt * 4 * tau * (1 - tau)
                x = x0 + dx * tau
                xi, yi = int(x), int(y)
                if 0 <= xi < W - 1 and 0 <= yi < H - 1:
                    col[yi:yi + 2, xi] = np.array([214, 220, 222], np.float32) * fl
                    sea_a[yi:yi + 2, xi] = True
        # niebla sobre el mar (se desliza despacio)
        if self.fog is not None:
            f = self.fog[:, (xs + int(t * 3)) % W]
            band = np.exp(-((yy - self.hy - 0.10 * H) / (0.12 * H)) ** 2)
            kf = (band * (0.25 + 0.75 * f) * 0.55)
            mm = sea_a | (depth >= 0)
            col[mm] = col[mm] * (1 - kf[mm, None]) + haze * fl * kf[mm, None]
        return sea_a
