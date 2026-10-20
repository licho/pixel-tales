"""Renderiza un episodio.

  python render.py series/survival/ep01.yaml              # video completo (con voz si existe)
  python render.py series/survival/ep01.yaml --fotos      # una imagen por panel (rápido, para revisar)
  python render.py series/survival/ep01.yaml --panel 2    # solo el panel 2 (sin voz)
"""
import argparse

from pixel_tales.video import render_episode

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episodio")
    ap.add_argument("--out")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--panel", type=int, help="número de panel (empieza en 1)")
    ap.add_argument("--fotos", action="store_true", help="exporta una imagen por panel en vez de video")
    a = ap.parse_args()
    render_episode(a.episodio, a.out, a.fps, None if a.panel is None else a.panel - 1, a.fotos)
