"""Llanura épica del mundo antiguo: cielo de atardecer, polvo, montañas, y extras opcionales.

Pensada para poner encima actores `ejercito` (multitudes), `estandarte` y sprites (elefante, legionario).

Parámetros:
  hora       'atardecer' | 'polvo' | 'anochecer' | 'noche' | 'tormenta'   (default atardecer)
  horizonte  fracción de H donde está el horizonte (default 0.42)
  sol        bool  disco de sol bajo (default true en atardecer)
  sol_x      fracción de W (default 0.62)
  montanas   bool  (default true)
  rio_seco   bool  cauce seco y agrietado que serpentea hasta el horizonte
  estrecho   [y0, y1] fracciones de H: franja de mar (Helesponto) que cruza la imagen
  puentes    [y, ...] fracciones de H: puentes de barcos horizontales sobre el estrecho
  ciudad     {x: 0.5, ancho: 0.6, alto: 0.05, tipo: 'china'|'oriental'}  ciudad amurallada en el horizonte
  huesos     bool  calaveras y huesos semienterrados (campo de Changping)
  lanzas_rotas int  lanzas clavadas/rotas en el suelo (default 0)
  milpa      bool  milpa seca en surcos (sequía)
  niebla     0-1   niebla baja sobre el suelo (default 0.25)
  semilla    int

Puntos útiles (vertical 256x384, horizonte 0.42 => y≈161):
  ejército en el suelo: zona [0, 166, 256, 330]   (y0 = cerca del horizonte, y1 = filas cercanas)
  puente en y=0.60H: cubierta de y-3 a y+1 (alto soldado ~6-9 px)
  estandartes en primer plano: pos [x, 0.95 H], alto 70-110
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.pintura import calavera, estrellas
from pixel_tales.scene import Scene

CIELOS = {
    #            arriba            medio             horizonte
    "atardecer": ((40, 34, 70), (168, 72, 40), (250, 180, 90)),
    "polvo": ((88, 62, 38), (180, 136, 86), (230, 196, 140)),
    "anochecer": ((18, 14, 28), (70, 36, 48), (150, 66, 46)),
    "noche": ((10, 10, 20), (26, 26, 46), (52, 50, 74)),
    "tormenta": ((16, 14, 22), (38, 34, 46), (74, 62, 70)),
}


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.08, "far": 0.2, "mid": 0.6, "fg": 1.2}

    def build(self):
        W, H = self.W, self.H
        p = self.p
        xx, yy = self.grid()
        rng = np.random.default_rng(70 + self.seed)
        hora = p.get("hora", "atardecer")
        top, mid, hor = (np.array(c, np.float32) for c in CIELOS.get(hora, CIELOS["atardecer"]))
        hy = float(p.get("horizonte", 0.42)) * H
        self.hy = hy

        # ---- cielo
        t = np.clip(yy / hy, 0, 1)[..., None]
        sky = np.where(t < 0.6, top * (1 - t / 0.6) + mid * (t / 0.6), mid * (1 - (t - 0.6) / 0.4) + hor * ((t - 0.6) / 0.4))
        nub = fbm(W, H, 11 + self.seed, (64, 32, 16))
        bandas = np.repeat(fbm(W // 4 + 1, H, 21 + self.seed, (16, 8, 4)), 4, axis=1)[:, :W]
        k = smooth(0.5, 0.75, nub * 0.5 + bandas * 0.5) * (yy < hy)
        if hora in ("atardecer", "polvo"):
            sky = sky * (1 - 0.35 * k[..., None]) + mid * 0.8 * 0.35 * k[..., None]
        else:
            sky = sky * (1 - 0.4 * k[..., None]) + np.array([60, 56, 70], np.float32) * 0.4 * k[..., None]
        sx, sy = float(p.get("sol_x", 0.62)) * W, hy - 0.035 * H
        if p.get("sol", hora == "atardecer"):
            dd = np.hypot(xx - sx, (yy - sy) * 1.1)
            sky += (np.exp(-dd / (0.25 * W)) * 70)[..., None] * np.array([1.0, 0.7, 0.35], np.float32)
            sky[dd < 0.06 * W] = (255, 228, 160)
            sky[(dd < 0.06 * W) & (yy > sy + 0.02 * H)] = (255, 200, 120)
        if hora == "noche":
            estrellas(self, sky, 0.004, hy / H * 0.8, self.seed, (200, 196, 210))
        self.sky = sky
        if hora == "tormenta":
            self.sky_flash = sky * 1.8 + np.array([40, 40, 60], np.float32)

        # ---- montañas lejanas
        if p.get("montanas", True):
            far = Image.new("L", (W, H), 0)
            fd = ImageDraw.Draw(far)
            for layer, amp in enumerate((0.07, 0.04)):
                pts = [(-5, hy + 2)]
                for x in np.linspace(-5, W + 5, 40):
                    pts.append((x, hy - amp * H * (0.5 + 0.5 * np.sin(x * 0.045 + layer * 2.3 + self.seed))
                                * (0.55 + 0.45 * np.cos(x * 0.017 + layer)) - rng.uniform(0, 1.5)))
                pts.append((W + 5, hy + 2))
                fd.polygon(pts, fill=100 + layer * 100)
            fa = np.asarray(far)
            self.far_a = fa > 0
            m1 = hor * 0.55 + top * 0.25
            m2 = hor * 0.75 + mid * 0.15
            self.far = np.where((fa > 150)[..., None], m2, m1).astype(np.float32) * np.ones((H, W, 1), np.float32)

        # ---- suelo
        u = np.clip((yy - hy) / (H - hy), 0, 1)
        n = fbm(W, H, 31 + self.seed, (32, 16, 8, 4))
        tierra_lejos = hor * 0.55 + np.array([60, 40, 20], np.float32) * 0.4
        tierra_cerca = np.array([88, 62, 38], np.float32) if hora in ("atardecer", "polvo") else np.array([46, 32, 30], np.float32) if hora == "anochecer" else np.array([40, 34, 34], np.float32)
        suelo = tierra_lejos * (1 - u[..., None] ** 0.6) + tierra_cerca * (u[..., None] ** 0.6)
        # surcos horizontales (perspectiva): ruido estirado en x
        surcos = np.repeat(vnoise(W // 8 + 1, H, 3, 41 + self.seed), 8, axis=1)[:, :W]
        suelo *= (0.82 + 0.22 * n + 0.1 * surcos)[..., None]
        alb = suelo.copy()
        a = yy >= hy

        img = Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        mk = Image.fromarray((a * 255).astype(np.uint8))
        dm = ImageDraw.Draw(mk)

        if p.get("rio_seco"):
            pts_l, pts_r = [], []
            for k2 in range(41):
                v = k2 / 40
                y = hy + 1 + (H - hy) * v ** 1.6
                cx = W * (0.5 + 0.22 * np.sin(v * 5.5 + self.seed) * v + 0.05 * np.sin(v * 13))
                w = 1 + W * 0.28 * v ** 1.4
                pts_l.append((cx - w, y))
                pts_r.append((cx + w, y))
            d.polygon(pts_l + pts_r[::-1], fill=(150, 112, 70) if hora != "noche" else (60, 50, 44))
            # grietas
            cm = Image.new("L", (W, H), 0)
            ImageDraw.Draw(cm).polygon(pts_l + pts_r[::-1], fill=255)
            cmask = np.asarray(cm) > 0
            cr = fbm(W, H, 51 + self.seed, (10, 5))
            arr = np.asarray(img, np.float32).copy()
            arr[cmask & (np.abs(cr - 0.5) < 0.018 + 0.02 * u)] *= 0.5
            arr[cmask & (yy < hy + 0.02 * H)] = arr[cmask & (yy < hy + 0.02 * H)] * 0.6 + hor * 0.4
            # piedras del cauce
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            d = ImageDraw.Draw(img)
            for _ in range(28):
                v = rng.uniform(0.2, 1.0)
                k2 = int(v * 40)
                y = pts_l[k2][1]
                x = rng.uniform(pts_l[k2][0], pts_r[k2][0])
                r = 0.5 + 3.5 * v ** 1.5
                d.ellipse([x - r, y - r * 0.5, x + r, y + r * 0.5], fill=(110, 92, 70))

        if p.get("estrecho"):
            y0, y1 = (f * H for f in p["estrecho"])
            arr = np.asarray(img, np.float32).copy()
            band = (yy >= y0) & (yy <= y1)
            v = np.clip((yy - y0) / max(y1 - y0, 1), 0, 1)
            agua = (hor * 0.55 * (1 - v[..., None]) + np.array([30, 36, 60], np.float32) * (0.6 + 0.4 * v[..., None]))
            ola = np.repeat(vnoise(W // 6 + 1, H, 2, 61 + self.seed), 6, axis=1)[:, :W]
            agua *= (0.85 + 0.3 * ola)[..., None]
            if p.get("sol", hora == "atardecer"):        # reflejo del sol
                ref = np.exp(-np.abs(xx - sx) / (0.05 * W + 0.15 * W * v)) * (ola > 0.55)
                agua += (ref * 120)[..., None] * np.array([1.0, 0.7, 0.35], np.float32)
            arr[band] = agua[band]
            # costa lejana con colinas
            for x in range(W):
                hh = 2 + 3 * (0.5 + 0.5 * np.sin(x * 0.08 + self.seed))
                arr[int(y0 - hh):int(y0) + 1, x] = hor * 0.45 + np.array([40, 30, 20], np.float32) * 0.5
            self.agua = band.copy()
            self.ola = ola
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            d = ImageDraw.Draw(img)
            for py in p.get("puentes", []):
                yb = py * H
                vv = (yb - y0) / max(y1 - y0, 1)
                bh = 1.5 + 5 * vv                       # alto de las barcas
                bw = 4 + 12 * vv                        # largo de cada barca
                x = -bw
                while x < W + bw:
                    d.chord([x, yb - bh * 0.4, x + bw * 0.92, yb + bh], 0, 180, fill=(60, 40, 26))
                    d.line([(x + bw * 0.45, yb - bh * 0.4), (x + bw * 0.45, yb - bh * 0.4 - bh * 0.8)], fill=(80, 56, 34))
                    x += bw
                self.agua &= ~((yy > yb - bh * 1.4) & (yy < yb + bh + 1))
                d.rectangle([0, yb - bh * 0.55, W, yb - bh * 0.25], fill=(116, 84, 50))      # cubierta de tablas
                d.line([(0, yb - bh * 0.55), (W, yb - bh * 0.55)], fill=(150, 110, 66))

        if p.get("ciudad"):
            c = p["ciudad"] if isinstance(p["ciudad"], dict) else {}
            cx, cw = c.get("x", 0.5) * W, c.get("ancho", 0.6) * W
            ch = c.get("alto", 0.05) * H
            base = hy + 2
            muro = (70, 58, 50) if hora != "noche" else (34, 30, 34)
            d.rectangle([cx - cw / 2, base - ch, cx + cw / 2, base], fill=muro)
            dm.rectangle([cx - cw / 2, base - ch - 20, cx + cw / 2, base], fill=255)
            for x in np.arange(cx - cw / 2, cx + cw / 2, 3):
                d.rectangle([x, base - ch - 1.5, x + 1.4, base - ch], fill=muro)
            for x in np.linspace(cx - cw / 2, cx + cw / 2, 6):
                d.rectangle([x - 3, base - ch * 1.6, x + 3, base], fill=tuple(int(v * 0.9) for v in muro))
                if c.get("tipo", "china") == "china":
                    d.polygon([(x - 6, base - ch * 1.6), (x + 6, base - ch * 1.6), (x + 3, base - ch * 1.6 - 3), (x - 3, base - ch * 1.6 - 3)],
                              fill=(40, 30, 30))
            # puerta central con techo curvo de dos pisos
            d.rectangle([cx - 4, base - ch * 0.7, cx + 4, base], fill=(20, 16, 16))
            if c.get("tipo", "china") == "china":
                for k2, (w2, y2) in enumerate(((16, ch * 1.9), (11, ch * 2.6))):
                    d.rectangle([cx - w2 * 0.6, base - y2, cx + w2 * 0.6, base - y2 + ch * 0.6], fill=(120, 40, 30))
                    d.polygon([(cx - w2, base - y2 + 1), (cx + w2, base - y2 + 1), (cx + w2 * 0.6, base - y2 - 3), (cx - w2 * 0.6, base - y2 - 3)],
                              fill=(36, 28, 28))
                    d.point([(cx - w2, base - y2), (cx + w2, base - y2)], fill=(36, 28, 28))
            # bruma sobre la ciudad
            arr = np.asarray(img, np.float32).copy()
            zone = (yy < base + 1) & (yy > base - ch * 3)
            arr[zone] = arr[zone] * 0.65 + hor * 0.35
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            d = ImageDraw.Draw(img)

        if p.get("huesos"):
            hueso = (196, 184, 152) if hora != "noche" else (150, 146, 140)
            for _ in range(90):
                v = rng.uniform(0.05, 1.0) ** 0.6
                y = hy + 2 + (H - hy - 4) * v
                x = rng.uniform(0, W)
                s = 0.4 + 2.2 * v
                r = rng.random()
                if r < 0.3:
                    calavera(d, x, y, s, hueso, (20, 14, 14))
                    d.rectangle([x - 4 * s, y + 1.2 * s, x + 4 * s, y + 4 * s], fill=tuple(int(c) for c in alb[min(int(y + 3), H - 1), int(x) % W]))
                elif r < 0.8:
                    L = (3 + 6 * rng.random()) * s
                    ang = rng.uniform(-0.6, 0.6)
                    d.line([(x, y), (x + np.cos(ang) * L, y + np.sin(ang) * L * 0.4)], fill=hueso, width=max(1, int(s)))
                else:                                    # costillas asomando
                    for j in range(4):
                        d.arc([x + j * 2 * s, y - 3 * s, x + j * 2 * s + 3 * s, y + 2 * s], 180, 300, fill=hueso)
            for _ in range(60):                          # pasto seco
                v = rng.uniform(0.3, 1.0)
                y = hy + (H - hy) * v
                x = rng.uniform(0, W)
                hgt = 2 + 8 * v * rng.random()
                d.line([(x, y), (x + rng.uniform(-2, 2), y - hgt)], fill=(84, 90, 52) if hora != "noche" else (40, 44, 34))

        if p.get("milpa"):                                        # milpa seca en surcos
            seca, seca_d = (176, 140, 82), (120, 90, 50)
            for k in range(14):
                v = (k + 1) / 14
                y = hy + 4 + (H - hy - 4) * v ** 1.5
                hgt = 2 + 46 * v ** 1.5
                esp = 3 + 16 * v ** 1.5
                x = rng.uniform(0, esp)
                while x < W:
                    if rng.random() < 0.85:
                        lean = rng.uniform(-0.25, 0.35) * hgt
                        top = (x + lean, y - hgt)
                        d.line([(x, y), top], fill=seca_d, width=max(1, int(v * 2.5)))
                        for j in range(1, 4):                     # hojas secas caídas
                            fy = y - hgt * j / 4
                            fx = x + lean * j / 4
                            sd = 1 if (j + int(x)) % 2 else -1
                            d.line([(fx, fy), (fx + sd * hgt * 0.28, fy + hgt * 0.12)], fill=seca if j % 2 else seca_d)
                    x += esp * rng.uniform(0.8, 1.2)
        for _ in range(int(p.get("lanzas_rotas", 0))):
            v = rng.uniform(0.1, 1.0) ** 0.7
            y = hy + 2 + (H - hy - 4) * v
            x = rng.uniform(0, W)
            L = (6 + 40 * v) * rng.uniform(0.5, 1.0)
            ang = rng.uniform(-0.5, 0.5)
            x2, y2 = x + np.sin(ang) * L, y - np.cos(ang) * L
            d.line([(x, y), (x2, y2)], fill=(70, 50, 30), width=max(1, int(0.5 + 1.5 * v)))
            if rng.random() < 0.4 and v > 0.4:                     # jirón de estandarte
                d.polygon([(x2, y2), (x2 + 8 * v, y2 + 3 * v), (x2 + 3 * v, y2 + 9 * v), (x2, y2 + 6 * v)], fill=(100, 30, 26))

        alb = np.asarray(img, np.float32).copy()

        # niebla baja / polvo en el horizonte
        nb = float(p.get("niebla", 0.25))
        if nb > 0:
            nf = fbm(W, H, 81 + self.seed, (48, 24, 12))
            kk = (np.exp(-((yy - hy) / (0.06 * H)) ** 2) * 0.8 + 0.25 * smooth(0.5, 0.8, nf) * (yy > hy)) * nb
            fogc = hor * 0.8 + np.array([40, 30, 20], np.float32) * 0.2
            alb = alb * (1 - kk[..., None]) + fogc * kk[..., None]
        self.mid_alb, self.mid_a = alb, np.asarray(mk) > 0

        # luz del sol rasante (cálida desde el horizonte) o fría de noche
        if hora == "anochecer":
            self.lights.append(Light("sol", self.point(sx, hy, 1.0 * max(W, H), 0.4), (0.9, 0.5, 0.4)))
        elif hora in ("atardecer", "polvo"):
            self.lights.append(Light("sol", self.point(sx, hy, 1.1 * max(W, H), 0.55), (1.0, 0.72, 0.42)))
        elif hora == "tormenta":
            self.lights.append(Light("cielo", self.point(0.5 * W, hy, 0.9 * H, 0.35), (0.6, 0.6, 0.8)))
        else:
            self.lights.append(Light("luna", self.point(0.5 * W, 0, 1.2 * H, 0.35), (0.55, 0.6, 0.85)))

    def animar(self, col, t):
        if getattr(self, "agua", None) is None:
            return
        m = self.agua & ~(self.depth > 0)
        xx, yy = self.grid()
        s = np.sin(xx[m] * 0.25 + yy[m] * 1.3 - t * 2.0 + self.ola[m] * 8)
        col[m] = np.where((s > 0.92)[..., None], col[m] * 1.35 + 10, col[m])
