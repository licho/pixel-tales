"""Convierte un episodio (YAML) en video: tiempos, capas, parallax, efectos, textos, voz."""
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

from .actors import MovingSprite, Sprite, draw_bats, draw_eyes, draw_scorpions, draw_zombie, rim_light
from .core import FORMATOS, S, Palette, ease, flicker
from .multitud import Ejercito, dibuja_estandarte
from .effects import Ash, Rain, Smoke, draw_flames

ROOT = Path(__file__).resolve().parent.parent
FADE = 0.35
CHARS_POR_SEG = 14.0     # velocidad aproximada de narración en español (sin voz)


def hup(a):
    """Escala solo en horizontal: la cámara se mueve en x, así se compone 5 veces más barato."""
    return np.repeat(a, S, 1)


class Style:
    def __init__(self, nombre):
        d = yaml.safe_load((ROOT / "styles" / f"{nombre}.yaml").read_text(encoding="utf-8"))
        self.nombre = d["nombre"]
        self.palette = Palette(d["paleta"], d.get("tramado", 13))
        self.ambiente = np.array(d.get("ambiente", [0.4, 0.55, 0.58]), np.float32)
        self.lluvia = np.array(d.get("lluvia", [110, 136, 128]), np.uint8)
        self.salpicadura = np.array(d.get("salpicadura", [146, 166, 156]), np.uint8)
        self.ceniza = np.array(d.get("ceniza", [120, 116, 110]), np.uint8)
        self.brasa = np.array(d.get("brasa", [236, 150, 60]), np.uint8)
        self.humo = tuple(d.get("humo", [70, 84, 84]))
        self.primer_plano = float(d.get("primer_plano", 0.6))
        self.texto = tuple(d.get("texto", [232, 222, 196]))
        self.acento = tuple(d.get("acento", [200, 50, 40]))
        self.fuente_texto = d.get("fuente_texto", "PixelifySans-Bold.woff")
        self.fuente_titulo = d.get("fuente_titulo", "Silkscreen-Bold.woff")


def load_scene(nombre, params, style, formato):
    path = ROOT / "scenes" / f"{nombre}.py"
    spec = importlib.util.spec_from_file_location(f"scenes.{nombre}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sc = mod.Escena(params, style, formato)
    sc.build()
    return sc


# ---------------------------------------------------------------- textos ---
class TextLayer:
    """Subtítulos y títulos con letra pixel, dibujados a resolución final."""

    def __init__(self, style, out_w, out_h, formato):
        self.style, self.W, self.H = style, out_w, out_h
        vert = formato == "vertical"
        self.f_sub = ImageFont.truetype(str(ROOT / "fonts" / style.fuente_texto), 60 if vert else 50)
        self.f_tit = ImageFont.truetype(str(ROOT / "fonts" / style.fuente_titulo), 64 if vert else 72)
        self.sub_y = int(out_h * (0.70 if vert else 0.86))
        self.tit_y = int(out_h * (0.15 if vert else 0.14))
        self.cache = {}

    def _sprite(self, text, font, color, maxw):
        key = (text, id(font), color)
        if key in self.cache:
            return self.cache[key]
        words, lines, cur = text.split(), [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if font.getlength(trial) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        lh = int(font.size * 1.25)
        wmax = int(max(font.getlength(l) for l in lines)) + 24
        im = Image.new("RGBA", (wmax, lh * len(lines) + 24), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.fontmode = "1"
        for i, l in enumerate(lines):
            d.text((wmax // 2, 12 + i * lh), l, font=font, fill=color + (255,), anchor="ma",
                   stroke_width=6, stroke_fill=(6, 4, 6, 255))
        arr = np.asarray(im)
        out = (arr[..., :3].copy(), arr[..., 3] > 127)
        self.cache[key] = out
        return out

    def _paste(self, frame, spr, cx, top):
        rgb, m = spr
        h, w = m.shape
        x0 = int(cx - w / 2)
        ya, yb = max(0, top), min(self.H, top + h)
        xa, xb = max(0, x0), min(self.W, x0 + w)
        if ya >= yb or xa >= xb:
            return
        np.copyto(frame[ya:yb, xa:xb], rgb[ya - top:yb - top, xa - x0:xb - x0],
                  where=m[ya - top:yb - top, xa - x0:xb - x0, None])

    def subtitle(self, frame, text, y=None):
        top = int(self.H * y) if y is not None else self.sub_y
        self._paste(frame, self._sprite(text, self.f_sub, self.style.texto, self.W * 0.86), self.W / 2, top)

    def title(self, frame, text, t):
        if t < 0.3:
            return
        spr = self._sprite(text, self.f_tit, self.style.acento, self.W * 0.9)
        shake = int(6 * max(0.0, 1 - (t - 0.3) / 0.25))
        self._paste(frame, spr, self.W / 2 + shake, self.tit_y - shake)


class Camcorder:
    """Interfaz de cámara de video encima del cuadro: esquinas, REC, contador; o PAUSA congelada."""

    def __init__(self, out_w, out_h):
        self.W, self.H = out_w, out_h
        self.f = ImageFont.truetype(str(ROOT / "fonts" / "Silkscreen-Bold.woff"), int(out_w * 0.045))

    def draw(self, frame, t, inicio=0.0, pausa=False):
        im = Image.fromarray(frame)
        d = ImageDraw.Draw(im)
        d.fontmode = "1"
        W, H = self.W, self.H
        m, L, w = int(W * 0.06), int(W * 0.09), max(4, W // 180)
        white = (236, 232, 220)
        for cx, cy, sx, sy in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
            d.line([(cx, cy), (cx + sx * L, cy)], fill=white, width=w)
            d.line([(cx, cy), (cx, cy + sy * L)], fill=white, width=w)
        tc = inicio + (0 if pausa else t)
        code = f"{int(tc // 3600):02d}:{int(tc // 60) % 60:02d}:{int(tc) % 60:02d}"
        d.text((W - m - L * 0.2, m + L * 0.6), code, font=self.f, fill=white, anchor="rm", stroke_width=3, stroke_fill=(0, 0, 0))
        if pausa:
            d.text((m + L * 0.2, m + L * 0.6), "|| PAUSA", font=self.f, fill=white, anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0))
        elif (t % 1.0) < 0.6:
            r = int(W * 0.018)
            d.ellipse([m + L * 0.25, m + L * 0.6 - r, m + L * 0.25 + 2 * r, m + L * 0.6 + r], fill=(200, 40, 30))
            d.text((m + L * 0.25 + 2.6 * r, m + L * 0.6), "REC", font=self.f, fill=white, anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0))
        arr = np.asarray(im).copy()
        rng = np.random.default_rng(int(t * 24) if not pausa else int(t * 6))
        for _ in range(3 if not pausa else 6):          # líneas de interferencia
            y = int(rng.integers(0, H - 6))
            arr[y:y + int(rng.integers(2, 6))] = np.clip(arr[y:y + 6][:1].astype(np.int16) + 40, 0, 255).astype(np.uint8)
        return arr


def digital_zoom(img, cx, cy, f):
    """Zoom digital: recorta alrededor de (cx, cy) en pixeles de salida y amplía sin suavizar."""
    h, w = img.shape[:2]
    cw, ch = int(w / f), int(h / f)
    x0 = int(min(max(cx - cw / 2, 0), w - cw))
    y0 = int(min(max(cy - ch / 2, 0), h - ch))
    crop = Image.fromarray(img[y0:y0 + ch, x0:x0 + cw])
    return np.asarray(crop.resize((w, h), Image.NEAREST))


def chunks(texto, max_words=6):
    """Parte la narración en pedazos cortos para subtítulos, cortando de preferencia en signos."""
    if not texto:
        return []
    parts = [p.strip() for p in re.split(r"(?<=[.,;:?!…])\s+", texto.strip()) if p.strip()]
    out = []
    for p in parts:
        w = p.split()
        n = max(1, -(-len(w) // max_words))
        size = -(-len(w) // n)
        out += [" ".join(w[i:i + size]) for i in range(0, len(w), size)]
    return out


# ----------------------------------------------------------------- panel ---
class PanelRenderer:
    def __init__(self, panel, style, formato):
        self.style, self.panel = style, panel
        pal = style.palette
        sc = load_scene(panel["escena"], panel.get("params"), style, formato)
        self.sc = sc
        self.LW, self.LH, self.VW, self.VH = FORMATOS[formato]
        ef = set(panel.get("efectos", []))
        self.parallax = sc.parallax
        self.pan = min(float(panel.get("camara", {}).get("pan", 12)), 25)

        self.sky = hup(pal.quantize(sc.sky))
        self.far = hup(pal.quantize(sc.far))
        self.far_a = hup(sc.far_a)
        self.relampago = "relampago" in ef
        if self.relampago:
            self.sky_f = hup(pal.quantize(getattr(sc, "sky_flash", None) if getattr(sc, "sky_flash", None) is not None
                                          else sc.sky * 2.1 + 30))
            self.far_f = hup(pal.quantize(sc.far * 0.55))

        alb, a, em = sc.mid_alb.copy(), sc.mid_a.copy(), sc.mid_em.copy()
        self.depth0 = np.full(a.shape, -1.0, np.float32)      # y de los pies de cada actor (-1 = nadie)
        self.dyn, self.eyes = [], []
        for act in panel.get("actores", []) or []:
            if "sprite" in act and ("movimiento" in act or "aparece" in act or "flota" in act or "desaparece" in act):
                self.dyn.append((MovingSprite(ROOT / "sprites" / f"{act['sprite']}.png", act), None))
            elif "sprite" in act:
                sp = Sprite(ROOT / "sprites" / f"{act['sprite']}.png")
                x, y = act["pos"]
                em_tmp = np.zeros_like(em)
                placed = sp.place(alb, a, x, y, act.get("escala", 1.0), act.get("espejo", False), em_tmp)
                alb[placed] *= float(act.get("brillo", 1.0))      # <1 = personaje en sombra
                self.depth0[placed] = y
                em[placed] = 0
                if act.get("contraluz", True):
                    rim_light(placed, em, sc.lights)
                em += em_tmp
            elif "zombi" in act:
                self.dyn.append((draw_zombie, act["zombi"]))
            elif "ejercito" in act:
                self.dyn.append((Ejercito(act["ejercito"], self.LW, self.LH), None))
            elif "estandarte" in act:
                self.dyn.append((dibuja_estandarte, act["estandarte"]))
            elif "murcielagos" in act:
                self.dyn.append((draw_bats, act["murcielagos"]))
            elif "escorpiones" in act:
                self.dyn.append((draw_scorpions, act["escorpiones"]))
            elif "ojos" in act:
                self.eyes.append(act["ojos"])
        self.alb, self.a, self.em = alb, a, em
        self.alb_u8 = np.clip(alb, 0, 255).astype(np.uint8)
        self.lights, self.fires = sc.lights, sc.fires
        self.parpadeo = "parpadeo" in ef
        self.smokes = [Smoke(f["x0"] + (f["x1"] - f["x0"]) * 0.4, f["y"] - 4, i, style.humo, f.get("tam", 1.0))
                       for i, f in enumerate(self.fires) if f.get("humo", True)]
        self.fg = hup(pal.quantize(sc.fg_alb * style.ambiente * style.primer_plano + 4))
        self.fg_a = hup(sc.fg_a)
        self.rain = Rain(self.VW, self.VH, **panel.get("lluvia", {})) if "lluvia" in ef else None
        self.ash = Ash(self.VW, self.VH) if "ceniza" in ef else None

    def mid_layer(self, t, fi, flash=False):
        LW, LH = self.LW, self.LH
        light = np.broadcast_to(self.style.ambiente, (LH, LW, 3)).copy()
        if flash:
            light += 0.55
        extra = np.zeros((LH, LW, 3), np.float32)
        for i, L in enumerate(self.lights):
            tipo = L.parpadeo if (L.parpadeo != "farol" or self.parpadeo) else None
            k = flicker(tipo, t, i * 1.9)
            light += L.rgb * k
            if L.volumen is not None:
                extra += L.volumen * k
        alb, a, em = self.alb, self.a, self.em
        if self.dyn:
            img = Image.fromarray(self.alb_u8.copy())
            zm = Image.new("L", (LW, LH), 0)
            depth = self.depth0.copy()
            for i, (fn, cfg) in enumerate(self.dyn):
                one = Image.new("L", (LW, LH), 0)
                fn(img, one, cfg, t, i)
                m1 = np.asarray(one) > 127
                depth[m1] = getattr(fn, "y", 1e6)
                zm.paste(255, (0, 0), one)
            zmask = np.asarray(zm) > 127
            self.sc.depth = depth
            alb = np.asarray(img, np.float32)
            a = a | zmask
            em = em * ~zmask[..., None]
        if not self.dyn:
            self.sc.depth = self.depth0
        col = alb * light + em + extra
        self.sc.flash = flash
        extra_a = self.sc.animar(col, t)
        if isinstance(extra_a, np.ndarray):
            a = a | extra_a
        for sm in self.smokes:
            sm.apply(col, t)
        rgb = self.style.palette.quantize(col)
        a = a.copy()
        for i, f in enumerate(self.fires):
            draw_flames(rgb, a, f, flicker("fuego", t, i * 2.3), fi)
        for i, e in enumerate(self.eyes):
            draw_eyes(rgb, a, e, t, i)
        return rgb, a

    def frame(self, t, dur, fi):
        e = ease(t / dur)
        lt = (t - dur * 0.55) % 7.3
        flash = self.relampago and (0 < lt < 0.1 or 0.2 < lt < 0.26)
        if self.relampago and self.panel.get("relampago_t") is not None:     # rayos en segundos exactos
            flash = any(0 < t - x < 0.1 or 0.2 < t - x < 0.26 for x in self.panel["relampago_t"])
        W = self.VW * S

        def ox(f):
            return int(round((6 + self.pan * self.parallax[f] * e) * S))

        o = ox("sky")
        frame = (self.sky_f if flash else self.sky)[:, o:o + W].copy()
        o = ox("far")
        src = self.far_f if flash else self.far
        np.copyto(frame, src[:, o:o + W], where=self.far_a[:, o:o + W, None])
        rgb, a = self.mid_layer(t, fi, flash)
        o = ox("mid")
        rgb, a = hup(rgb), hup(a)
        np.copyto(frame, rgb[:, o:o + W], where=a[:, o:o + W, None])
        o = ox("fg")
        np.copyto(frame, self.fg[:, o:o + W], where=self.fg_a[:, o:o + W, None])
        if self.rain is not None:
            streak, splash = self.rain.masks(t, fi)
            frame[hup(streak)] = self.style.lluvia
            frame[hup(splash)] = self.style.salpicadura
        if self.ash is not None:
            ash, ember = self.ash.masks(t)
            frame[hup(ash)] = self.style.ceniza
            frame[hup(ember)] = self.style.brasa
        return np.repeat(frame, S, 0)


# --------------------------------------------------------------- episodio ---
def audio_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def plan_durations(ep, voz):
    """'duracion' numérica se respeta. Con voz, el resto se reparte el audio según su texto;
    sin voz, se estima por el largo del texto."""
    panels = ep["paneles"]
    fixed = [p.get("duracion") if isinstance(p.get("duracion"), (int, float)) else None for p in panels]
    if voz is None:
        return [d if d is not None else max(3.0, len(p.get("texto", "")) / CHARS_POR_SEG + 1.0)
                for p, d in zip(panels, fixed)]
    total = audio_duration(voz)
    rest = max(total - sum(d for d in fixed if d), 2.0 * fixed.count(None))
    weights = [max(len(p.get("texto", "")), 1) for p, d in zip(panels, fixed) if d is None]
    wsum = sum(weights)
    it = iter(weights)
    return [d if d is not None else rest * next(it) / wsum for d in fixed]


def sync_words(ep, words_path, audio_len):
    """Con los tiempos por palabra (JSON de ElevenLabs), calcula la duración exacta de cada panel
    y el momento en que aparece cada subtítulo. Devuelve (duraciones, [[(t0, t1, texto)...] por panel])
    o None si el texto no coincide con la transcripción."""
    data = json.loads(Path(words_path).read_text(encoding="utf-8"))
    words = [w for w in (data.get("words", data) if isinstance(data, dict) else data) if w.get("type", "word") == "word"]
    panels = ep["paneles"]
    counts = [len(p.get("texto", "").split()) for p in panels]
    if sum(counts) != len(words):
        print(f"Aviso: el texto tiene {sum(counts)} palabras y el audio {len(words)}; uso reparto aproximado.")
        return None
    LEAD = 0.25                                   # el panel cambia un poco antes de su primera palabra
    starts, i = [], 0
    for c in counts:
        starts.append(words[i]["start"] if c else (starts[-1] if starts else 0.0))
        i += c
    bounds = [0.0] + [max(0.0, s - LEAD) for s in starts[1:]] + [max(audio_len, words[-1]["end"] + 0.8)]
    durs = [b - a for a, b in zip(bounds, bounds[1:])]
    subs, i = [], 0
    for k, (p, c) in enumerate(zip(panels, counts)):
        pw = words[i:i + c]
        i += c
        out, j = [], 0
        cs = chunks(p.get("texto", ""))
        for n, ch in enumerate(cs):
            m = len(ch.split())
            t0 = pw[j]["start"] - bounds[k]
            t1 = (pw[j + m]["start"] - bounds[k]) if j + m < len(pw) else durs[k] - 0.2
            out.append((t0, t1, ch))
            j += m
        subs.append(out)
    return durs, subs


def subtitle_at(texto, t, dur):
    cs = chunks(texto)
    if not cs:
        return None
    a, b = 0.15, max(dur - 0.25, 0.3)
    tot = sum(len(c) for c in cs)
    acc = a
    for c in cs:
        span = (b - a) * len(c) / tot
        if t < acc + span:
            return c if t >= a else None
        acc += span
    return None


def render_episode(ep_path, out=None, fps=24, solo_panel=None, fotos=False):
    ep_path = Path(ep_path)
    ep = yaml.safe_load(ep_path.read_text(encoding="utf-8"))
    style = Style(ep["estilo"])
    formato = ep.get("formato", "horizontal")
    _, _, VW, VH = FORMATOS[formato]
    OW, OH = VW * S, VH * S
    subs = ep.get("subtitulos", formato == "vertical")
    texts = TextLayer(style, OW, OH, formato)
    voz = ep.get("voz")
    voz = (ep_path.parent / voz) if voz else None
    if voz is not None and not voz.exists():
        print(f"Aviso: no encontré la voz {voz}; estimo duraciones por el texto.")
        voz = None
    durs = plan_durations(ep, voz)
    timed = None
    if voz is not None and ep.get("palabras"):
        wp = ep_path.parent / ep["palabras"]
        if wp.exists():
            res = sync_words(ep, wp, audio_duration(voz))
            if res:
                durs, timed = res
                print("Sincronizado por palabras.")
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    name = f"{ep_path.parent.name}_{ep_path.stem}"

    cam = Camcorder(OW, OH)

    def overlay(img, panel, t, dur, idx=None):
        ef = panel.get("efectos", [])
        if panel.get("zoom"):
            z = panel["zoom"]
            f0 = z.get("factor", 3)
            f = f0 + (z.get("factor_final", f0) - f0) * ease(t / dur)       # acercamiento lento opcional
            img[:] = digital_zoom(img, (z["centro"][0] - 6) * S, z["centro"][1] * S, f)
        if "grabacion" in ef or "pausa" in ef:
            img[:] = cam.draw(img, t, panel.get("grabacion_inicio", 0.0), "pausa" in ef)
        if panel.get("titulo"):
            texts.title(img, panel["titulo"], t)
        if subs:
            if timed is not None and idx is not None:
                s = next((c for a, b, c in timed[idx] if a <= t < b), None)
            else:
                s = subtitle_at(panel.get("texto", ""), t, dur)
            if s:
                texts.subtitle(img, s, panel.get("subtitulos_y"))

    idxs = [solo_panel] if solo_panel is not None else range(len(ep["paneles"]))
    if fotos:
        for i in idxs:
            p = ep["paneles"][i]
            r = PanelRenderer(p, style, formato)
            t = durs[i] * 0.5
            img = r.frame(t, durs[i], 0)
            overlay(img, p, max(t, 1.0), durs[i], i)
            path = out_dir / f"{name}_panel{i + 1:02d}.png"
            Image.fromarray(img).save(path)
            print("Foto:", path)
        return

    out = Path(out) if out else out_dir / f"{name}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{OW}x{OH}", "-r", str(fps), "-i", "-"]
    if voz is not None and solo_panel is None:
        cmd += ["-i", str(voz), "-map", "0:v", "-map", "1:a", "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    fi = 0
    for i in idxs:
        p = ep["paneles"][i]
        r = PanelRenderer(p, style, formato)
        dur = durs[i]
        n = int(round(dur * fps))
        print(f"Panel {i + 1}/{len(ep['paneles'])}: {p['escena']} ({dur:.1f}s)")
        for k in range(n):
            t = k / fps
            img = r.frame(0.4 if p.get("congelado") else t, dur, fi if not p.get("congelado") else 0)
            overlay(img, p, t, dur, i)
            fade = min(1.0, t / FADE, (dur - t) / FADE)
            if fade < 1:
                img = (img.astype(np.float32) * max(fade, 0)).astype(np.uint8)
            ff.stdin.write(img.tobytes())
            fi += 1
    ff.stdin.close()
    ff.wait()
    print("Listo:", out)
    return out
