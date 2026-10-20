# Instrucciones para Claude

Repo para crear videos de historias en pixel art con voz (series: survival, leyendas prehispánicas, nahuales…).
El usuario es Luis; respóndele en español y con explicaciones sencillas.

## Para ahorrar tokens
- **Para escribir o editar un episodio: lee solo `CATALOGO.md`** y el YAML del episodio. No abras el motor ni las escenas.
- Revisa resultados con `python render.py <episodio> --fotos` (una imagen por panel, tarda segundos) antes de renderizar el video.
- Abre `pixel_tales/` o `scenes/*.py` solo si hay que crear algo nuevo o corregir un error.

## Al crear piezas nuevas
- Escena nueva: `scenes/<nombre>.py` con `class Escena(Scene)` (ver docstring de `pixel_tales/scene.py`). Pinta a 424x216 con colores "reales"; la paleta del estilo se aplica sola.
- Sprite nuevo: PNG RGBA con colores base (sin luz) en `sprites/<serie>/`, y un `.json` con `{"ancla": [x_pies, y_pies]}`. Si se genera con código, guarda el script en `tools/`.
- Estilo nuevo: `styles/<nombre>.yaml` (paleta, tramado, luz ambiental).
- **Siempre actualiza `CATALOGO.md`** con lo nuevo (nombre, parámetros y dónde colocar actores).

## Comandos
- `pip install -r requirements.txt` (y ffmpeg instalado)
- `python render.py series/<serie>/<ep>.yaml` → `output/<serie>_<ep>.mp4`
- `--fotos` para imágenes por panel, `--panel N` para un solo panel
