"""Convierte un episodio (YAML) en video: tiempos, capas, parallax, efectos, voz."""
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from .actors import Sprite, draw_zombie, rim_light
from .core import LW, LH, VW, VH, S, Palette, ease, flicker


def hup(a):
    """Escala solo en horizontal: la cámara se mueve en x, así se compone 5 veces más barato."""
    return np.repeat(a, S, 1)
from .effects import Rain, Smoke, draw_flames

ROOT = Path(__file__).resolve().parent.parent
FADE = 0.35


class Style:
    def __init__(self, nombre):
        d = yaml.safe_load((ROOT / "styles" / f"{nombre}.yaml").read_text(encoding="utf-8"))
        self.nombre = d["nombre"]
        self.palette = Palette(d["paleta"], d.get("tramado", 13))
        self.ambiente = np.array(d.get("ambiente", [0.4, 0.55, 0.58]), np.float32)
        self.lluvia = np.array(d.get("lluvia", [110, 136, 128]), np.uint8)
        self.salpicadura = np.array(d.get("salpicadura", [146, 166, 156]), np.uint8)
        self.humo = tuple(d.get("humo", [70, 84, 84]))
        self.primer_plano = float(d.get("primer_plano", 0.6))


def load_scene(nombre, params, style):
    path = ROOT / "scenes" / f"{nombre}.py"
    spec = importlib.util.spec_from_file_location(f"scenes.{nombre}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sc = mod.Escena(params, style)
    sc.build()
    return sc


class PanelRenderer:
    def __init__(self, panel, style):
        self.style = style
        pal = style.palette
        sc = load_scene(panel["escena"], panel.get("params"), style)
        ef = set(panel.get("efectos", []))
        self.parallax = sc.parallax
        self.pan = min(float(panel.get("camara", {}).get("pan", 18)), 25)

        self.sky = hup(pal.quantize(sc.sky))
        self.far = hup(pal.quantize(sc.far))
        self.far_a = hup(sc.far_a)
        self.relampago = "relampago" in ef
        if self.relampago:
            self.sky_f = hup(pal.quantize(sc.sky * 2.1 + 30))
            self.far_f = hup(pal.quantize(sc.far * 0.55))

        alb, a, em = sc.mid_alb.copy(), sc.mid_a.copy(), sc.mid_em.copy()
        self.zombies = []
        for act in panel.get("actores", []) or []:
            if "sprite" in act:
                sp = Sprite(ROOT / "sprites" / f"{act['sprite']}.png")
                x, y = act["pos"]
                placed = sp.place(alb, a, x, y, act.get("escala", 1.0), act.get("espejo", False))
                em[placed] = 0
                rim_light(placed, em, sc.lights)
            elif "zombi" in act:
                self.zombies.append(act["zombi"])
        self.alb, self.a, self.em = alb, a, em
        self.alb_u8 = np.clip(alb, 0, 255).astype(np.uint8)
        self.lights, self.fires = sc.lights, sc.fires
        self.parpadeo = "parpadeo" in ef
        self.smokes = [Smoke(f["x0"] + (f["x1"] - f["x0"]) * 0.4, f["y"] - 4, i, style.humo)
                       for i, f in enumerate(self.fires) if f.get("humo", True)]
        self.fg = hup(pal.quantize(sc.fg_alb * style.ambiente * style.primer_plano + 4))
        self.fg_a = hup(sc.fg_a)
        self.rain = Rain() if "lluvia" in ef else None

    def mid_layer(self, t, fi):
        light = np.broadcast_to(self.style.ambiente, (LH, LW, 3)).copy()
        extra = np.zeros((LH, LW, 3), np.float32)
        for L in self.lights:
            tipo = L.parpadeo if (L.parpadeo != "farol" or self.parpadeo) else None
            k = flicker(tipo, t)
            light += L.rgb * k
            if L.volumen is not None:
                extra += L.volumen * k
        alb, a, em = self.alb, self.a, self.em
        if self.zombies:
            img = Image.fromarray(self.alb_u8.copy())
            zm = Image.new("L", (LW, LH), 0)
            for i, z in enumerate(self.zombies):
                draw_zombie(img, zm, z, t, i)
            zmask = np.asarray(zm) > 127
            alb = np.asarray(img, np.float32)
            a = a | zmask
            em = em * ~zmask[..., None]
        col = alb * light + em + extra
        for sm in self.smokes:
            sm.apply(col, t)
        rgb = self.style.palette.quantize(col)
        a = a.copy()
        for f in self.fires:
            draw_flames(rgb, a, f, flicker("fuego", t), fi)
        return rgb, a

    def frame(self, t, dur, fi):
        e = ease(t / dur)
        lt = (t - dur * 0.55) % 7.3
        flash = self.relampago and (0 < lt < 0.1 or 0.2 < lt < 0.26)
        W = VW * S

        def ox(f):
            return int(round((6 + self.pan * self.parallax[f] * e) * S))

        o = ox("sky")
        frame = (self.sky_f if flash else self.sky)[:, o:o + W].copy()
        o = ox("far")
        src = self.far_f if flash else self.far
        m = self.far_a[:, o:o + W]
        np.copyto(frame, src[:, o:o + W], where=m[..., None])
        rgb, a = self.mid_layer(t, fi)
        o = ox("mid")
        rgb, a = hup(rgb), hup(a)
        np.copyto(frame, rgb[:, o:o + W], where=a[:, o:o + W, None])
        o = ox("fg")
        np.copyto(frame, self.fg[:, o:o + W], where=self.fg_a[:, o:o + W, None])
        if self.rain is not None:
            streak, splash = self.rain.masks(t, fi)
            frame[hup(streak)] = self.style.lluvia
            frame[hup(splash)] = self.style.salpicadura
        return np.repeat(frame, S, 0)


# --------------------------------------------------------------- episodio ---
def audio_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def plan_durations(ep, voz):
    """Paneles con 'duracion' numérica la respetan; los demás se reparten el audio según su texto."""
    panels = ep["paneles"]
    fixed = [p.get("duracion") if isinstance(p.get("duracion"), (int, float)) else None for p in panels]
    if voz is None:
        return [d if d is not None else 6.0 for d in fixed]
    total = audio_duration(voz)
    rest = max(total - sum(d for d in fixed if d), 2.0 * fixed.count(None))
    weights = [max(len(p.get("texto", "")), 1) for p, d in zip(panels, fixed) if d is None]
    wsum = sum(weights)
    it = iter(weights)
    return [d if d is not None else rest * next(it) / wsum for d in fixed]


def render_episode(ep_path, out=None, fps=24, solo_panel=None, fotos=False):
    ep_path = Path(ep_path)
    ep = yaml.safe_load(ep_path.read_text(encoding="utf-8"))
    style = Style(ep["estilo"])
    voz = ep.get("voz")
    voz = (ep_path.parent / voz) if voz else None
    if voz is not None and not voz.exists():
        print(f"Aviso: no encontré la voz {voz}; uso duraciones por defecto.")
        voz = None
    durs = plan_durations(ep, voz)
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    name = f"{ep_path.parent.name}_{ep_path.stem}"

    idxs = [solo_panel] if solo_panel is not None else range(len(ep["paneles"]))
    if fotos:
        for i in idxs:
            r = PanelRenderer(ep["paneles"][i], style)
            img = r.frame(durs[i] * 0.5, durs[i], 0)
            p = out_dir / f"{name}_panel{i + 1:02d}.png"
            Image.fromarray(img).save(p)
            print("Foto:", p)
        return

    out = Path(out) if out else out_dir / f"{name}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{VW * S}x{VH * S}", "-r", str(fps), "-i", "-"]
    if voz is not None and solo_panel is None:
        cmd += ["-i", str(voz), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    fi = 0
    for i in idxs:
        r = PanelRenderer(ep["paneles"][i], style)
        dur = durs[i]
        n = int(round(dur * fps))
        print(f"Panel {i + 1}/{len(ep['paneles'])}: {ep['paneles'][i]['escena']} ({dur:.1f}s)")
        for k in range(n):
            t = k / fps
            img = r.frame(t, dur, fi)
            fade = min(1.0, t / FADE, (dur - t) / FADE)
            if fade < 1:
                img = (img.astype(np.float32) * max(fade, 0)).astype(np.uint8)
            ff.stdin.write(img.tobytes())
            fi += 1
    ff.stdin.close()
    ff.wait()
    print("Listo:", out)
    return out
