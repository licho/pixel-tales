# pixel-tales

Motor para crear videos de historias ilustradas en **pixel art** con voz encima: paneles con parallax, lluvia, fuego, humo, luces que parpadean y personajes con movimiento sencillo. Sirve para videos largos sin que el costo crezca, porque no usa video generado por IA.

## Cómo funciona
1. **Escenas** (`scenes/`): fondos reutilizables pintados con código (calle, bosque, lago…), con parámetros.
2. **Estilos** (`styles/`): la paleta y la luz de cada serie. El mismo fondo cambia de look según el estilo.
3. **Sprites** (`sprites/`): personajes y objetos en PNG.
4. **Episodios** (`series/<serie>/epXX.yaml`): qué escena, qué personajes y qué texto va en cada panel.

Todo se pinta a baja resolución (384x216 horizontal o 216x384 vertical) y se escala x5 a 1920x1080 / 1080x1920 sin suavizar, con paleta fija y tramado. Incluye subtítulos y título con letra pixel (fuentes OFL en `fonts/`).

## Uso
```bash
pip install -r requirements.txt     # requiere ffmpeg
python render.py series/survival/ep01.yaml --fotos   # vista rápida: una imagen por panel
python render.py series/survival/ep01.yaml           # video en output/
```

Con voz: pon el audio junto al episodio (`voz: ep01.mp3`) y escribe el `texto` de cada panel. El motor reparte la duración del audio según lo largo de cada texto.

Velocidad aproximada: 1.3x la duración del video (10 min de video ≈ 13 min de render).

## Render en GitHub
La acción **Render episodio** genera el video cuando subes o cambias un `series/**/*.yaml`, o a mano desde la pestaña *Actions*. El MP4 queda como artefacto descargable del run.

Ver `CATALOGO.md` para todo lo disponible.
