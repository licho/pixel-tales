"""Genera las piezas de marca del canal con el motor: portada de Facebook, banner de YouTube
y foto de perfil. Salen en output/marca/.

  python tools/portada.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pixel_tales.video import PanelRenderer, Style  # noqa: E402

OUT = ROOT / "output" / "marca"
FONTS = ROOT / "fonts"
TITULO = "PIXEL TALES"
LEMA = "Historias de terror, leyendas y supervivencia"


def panel(formato, horizonte, escala, W, H):
    """Panorama + actores colocados en coordenadas relativas al tamaño de la capa."""
    k, hy, cx = escala, horizonte * H, W / 2
    return {
        "escena": "panorama",
        "params": {"horizonte": horizonte, "escala": escala},
        "efectos": ["ceniza"],
        "camara": {"pan": 0},
        "actores": [
            {"sprite": "survival/sobreviviente_traje", "pos": [round(cx - 0.62 * k), round(hy + 0.10 * k)],
             "escala": round(0.0030 * k, 3)},
            {"sprite": "xibalba/gemelo", "pos": [round(cx - 0.16 * k), round(hy + 0.12 * k)], "escala": round(0.0026 * k, 3)},
            {"sprite": "xibalba/gemelo", "pos": [round(cx + 0.16 * k), round(hy + 0.12 * k)], "escala": round(0.0026 * k, 3),
             "espejo": True},
            {"ojos": {"pos": [round(cx + 0.78 * k), round(hy - 0.05 * k)], "color": [236, 190, 60], "separacion": 3}},
            {"ojos": {"pos": [round(cx + 0.95 * k), round(hy - 0.02 * k)], "color": [255, 70, 40], "separacion": 3}},
        ],
    }


def texto(img, titulo_px, lema_px, cy_titulo, cy_lema, ancho_max):
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    W = img.width
    ft = ImageFont.truetype(str(FONTS / "Silkscreen-Bold.woff"), titulo_px)
    while ft.getlength(TITULO) > ancho_max:
        titulo_px -= 4
        ft = ImageFont.truetype(str(FONTS / "Silkscreen-Bold.woff"), titulo_px)
    sh = max(4, titulo_px // 12)
    d.text((W / 2 + sh, cy_titulo + sh), TITULO, font=ft, anchor="mm", fill=(150, 30, 24),
           stroke_width=sh, stroke_fill=(6, 4, 6))
    d.text((W / 2, cy_titulo), TITULO, font=ft, anchor="mm", fill=(232, 220, 190), stroke_width=sh, stroke_fill=(6, 4, 6))
    if lema_px:
        fl = ImageFont.truetype(str(FONTS / "PixelifySans-Bold.woff"), lema_px)
        while fl.getlength(LEMA) > ancho_max:
            lema_px -= 2
            fl = ImageFont.truetype(str(FONTS / "PixelifySans-Bold.woff"), lema_px)
        d.text((W / 2, cy_lema), LEMA, font=fl, anchor="mm", fill=(236, 190, 96),
               stroke_width=max(3, lema_px // 10), stroke_fill=(6, 4, 6))


def render(formato, horizonte, escala, t=1.2):
    from pixel_tales.core import FORMATOS
    W, H, VW, VH = FORMATOS[formato]
    style = Style("pixeltales")
    r = PanelRenderer(panel(formato, horizonte, escala, W, H), style, formato)
    return Image.fromarray(r.frame(t, 10.0, 7))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)

    # Facebook: 1640x624. Lo importante dentro del centro 1280x624 (se recorta en celular).
    fb = render("portada_fb", 0.80, 112).crop((0, 0, 1640, 624))
    texto(fb, 120, 40, 120, 205, 1180)
    fb.save(OUT / "portada_facebook_1640x624.png")

    # YouTube: 2560x1440. Zona visible en todos los dispositivos: 1546x423 al centro (y 508-931).
    yt = render("banner_yt", 0.645, 150)
    texto(yt, 150, 52, 640, 760, 1450)
    yt.save(OUT / "banner_youtube_2560x1440.png")

    # Perfil: 1080x1080 sin texto (el nombre ya aparece junto a la foto). Se ve en círculo.
    pf = render("cuadrado", 0.76, 200)
    pf.save(OUT / "perfil_1080.png")

    for f in sorted(OUT.glob("*.png")):
        print("Listo:", f.relative_to(ROOT), Image.open(f).size)
