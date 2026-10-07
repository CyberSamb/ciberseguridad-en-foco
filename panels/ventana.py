"""
panels/ventana.py
Estética de "ventana" decorativa compartida por los paneles: una barra superior con puntos de
colores a la izquierda, una barra de búsqueda opcional junto a los puntos y los íconos de minimizar,
redimensionar y cerrar a la derecha. Nada de esto es funcional: no hay ningún control, está
oculto para lectores de pantalla y no responde al mouse.
"""

GRIS = "#8b8fa3"


def una_linea(html):
    """Colapsa HTML a una línea: Markdown trata como código las líneas con 4+ espacios de sangría."""
    return " ".join(linea.strip() for linea in html.splitlines() if linea.strip())


def barra_ventana(puntos, buscador=False):
    """HTML de la barra de ventana. `puntos`: colores de los círculos de la izquierda."""
    circulos = "".join(
        f'<span style="width:12px; height:12px; border-radius:50%; background:{c}; display:inline-block;"></span>'
        for c in puntos
    )
    busqueda = ""
    if buscador:
        busqueda = (
            '<div style="width:100%; max-width:20rem; margin-left:1.2rem; '
            f'border:1px solid rgba(255,255,255,0.18); border-radius:999px; padding:0.2rem 1rem; color:{GRIS}; font-size:0.8rem;">'
            'Buscar...</div>'
        )
    return una_linea(
        '<div aria-hidden="true" style="display:flex; justify-content:space-between; align-items:center; '
        'margin:0 0.4rem 0.6rem 0.4rem; user-select:none; pointer-events:none;">'
        f'<div style="flex:1; display:flex; align-items:center;"><div style="display:flex; gap:0.5rem; flex:none;">{circulos}</div>{busqueda}</div>'
        f'<div style="display:flex; gap:0.9rem; color:{GRIS}; font-size:0.8rem; line-height:1; flex:none; margin-left:1rem;">'
        '<span>&#8212;</span><span>&#9632;</span><span>&#10006;</span></div></div>'
    )