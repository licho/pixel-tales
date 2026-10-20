"""Usa una imagen como fondo (por ejemplo, una ilustración generada con Gemini) y la pasa por la paleta y el
tramado del estilo, para que combine con el resto del canal. Encima funcionan lluvia, relámpago, ceniza,
niebla, cámara, zoom, ojos, etc.

Parámetros:
  archivo       ruta dentro del repo (ej. fondos/nahuales/el_doble/panel09.png)
  zoom          [inicio, fin]  acercamiento lento durante el panel (1 = imagen completa) (default [1, 1])
  foco          [x, y] relativos (0-1) del centro al inicio (default [0.5, 0.5])
  foco_final    [x, y] relativos al final (default = foco)  -> paneo lento
  alternativa   {archivo: ..., intervalos: [[t0, t1], ...]}  muestra otra imagen en esos segundos
  luces         [{pos: [x, y], radio: px, color: [r, g, b], intensidad, parpadeo: fuego|farol}]
                pos y radio en PÍXELES DE LA IMAGEN ORIGINAL
  brillo        multiplica la luz de la imagen (default 1.0)

Importante: los actores `ojos` en un panel con esta escena usan `pos` en PÍXELES DE LA IMAGEN ORIGINAL
y siguen al zoom/paneo. Usa `camara: {pan: 0}` (el movimiento lo da el zoom/foco).
Limitación: es una sola capa, sin parallax por profundidad.
"""
from pathlib import Path

import numpy as np
from PIL import Image

from pixel_tales.core import Light, ease
from pixel_tales.scene import Scene

ROOT = Path(__file__).resolve().parent.parent
OX = 6          # columna de la capa donde empieza la vista de la cámara con pan 0


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.0, "far": 0.0, "mid": 0.0, "fg": 0.0}

    def _carga(self, ruta):
        return Image.open(ROOT / ruta).convert("RGB")

    def build(self):
        p = self.p
        self.src = self._carga(p["archivo"])
        alt = p.get("alternativa")
        self.alt = self._carga(alt["archivo"]) if alt else None
        self.intervalos = alt.get("intervalos", []) if alt else []
        self.z0, self.z1 = p.get("zoom", [1.0, 1.0])
        self.f0 = p.get("foco", [0.5, 0.5])
        self.f1 = p.get("foco_final", self.f0)
        self.k = float(p.get("brillo", 1.0))
        iw, ih = self.src.size
        self.base = max(self.VW / iw, self.VH / ih)          # escala para cubrir la vista
        self.dur = 6.0
        self.mid_a[:] = True
        self.mid_alb = self._cuadro(0.0, self.src) / self.style.ambiente[None, None, :] * self.k
        for L in p.get("luces", []):
            x, y = self.mapear(L["pos"], 0.0)
            r = L.get("radio", 60) * self.base
            self.lights.append(Light("luz", self.point(x, y, r, L.get("intensidad", 0.6)),
                                     tuple(np.array(L.get("color", [255, 190, 120])) / 255), parpadeo=L.get("parpadeo")))

    def _ventana(self, t):
        e = ease(t / max(self.dur, 0.01))
        z = self.z0 + (self.z1 - self.z0) * e
        fx = self.f0[0] + (self.f1[0] - self.f0[0]) * e
        fy = self.f0[1] + (self.f1[1] - self.f0[1]) * e
        iw, ih = self.src.size
        s = self.base * z
        cw, ch = self.VW / s, self.VH / s
        x0 = min(max(fx * iw - cw / 2, 0), iw - cw)
        y0 = min(max(fy * ih - ch / 2, 0), ih - ch)
        return x0, y0, s

    def mapear(self, pos, t):
        """Píxeles de la imagen original -> píxeles de la capa, con el zoom/paneo del momento t."""
        x0, y0, s = self._ventana(t)
        return OX + (pos[0] - x0) * s, (pos[1] - y0) * s

    def _cuadro(self, t, im):
        x0, y0, s = self._ventana(t)
        crop = im.crop((x0, y0, x0 + self.VW / s, y0 + self.VH / s)).resize((self.VW, self.VH), Image.BOX)
        v = np.asarray(crop, np.float32)
        out = np.empty((self.H, self.W, 3), np.float32)
        out[:, OX:OX + self.VW] = v
        out[:, :OX] = v[:, :1]
        out[:, OX + self.VW:] = v[:, -1:]
        return out

    def animar(self, col, t):
        self.dur = getattr(self, "dur_panel", self.dur)
        im = self.src
        if self.alt is not None and any(a <= t < b for a, b in self.intervalos):
            im = self.alt
        if self.z0 == self.z1 and self.f0 == self.f1 and im is self.src:
            return None                                      # imagen fija: ya está en mid_alb
        luz = getattr(self, "light", None)
        arr = self._cuadro(t, im) / self.style.ambiente[None, None, :] * self.k
        col[:] = arr * (luz if luz is not None else self.style.ambiente[None, None, :])
        return None
