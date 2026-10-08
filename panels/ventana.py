"""
panels/ventana.py
Estética de "ventana" decorativa compartida por los paneles: una barra superior con puntos de
colores a la izquierda, una barra de búsqueda opcional junto a los puntos y los íconos de minimizar,
redimensionar y cerrar a la derecha. Nada de esto es funcional: no hay ningún control, está
oculto para lectores de pantalla y no responde al mouse.
"""

import html
from contextlib import contextmanager

import streamlit as st

GRIS = "#8b8fa3"


def una_linea(html):
    """Colapsa HTML a una línea: Markdown trata como código las líneas con 4+ espacios de sangría."""
    return " ".join(linea.strip() for linea in html.splitlines() if linea.strip())


def barra_ventana(puntos, buscador=False, liviana=False):
    """HTML de la barra de ventana. `puntos`: colores de los círculos de la izquierda.
    `liviana`: versión fina (puntos y íconos más chicos) para marcar cada gráfico."""
    d = 9 if liviana else 12
    margen = "0 0.3rem 0.1rem 0.3rem" if liviana else "0 0.4rem 0.6rem 0.4rem"
    tam_icono = "0.68rem" if liviana else "0.8rem"
    sep_icono = "0.7rem" if liviana else "0.9rem"
    circulos = "".join(
        f'<span style="width:{d}px; height:{d}px; border-radius:50%; background:{c}; display:inline-block;"></span>'
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
        f'margin:{margen}; user-select:none; pointer-events:none;">'
        f'<div style="flex:1; display:flex; align-items:center;"><div style="display:flex; gap:0.5rem; flex:none;">{circulos}</div>{busqueda}</div>'
        f'<div style="display:flex; gap:{sep_icono}; color:{GRIS}; font-size:{tam_icono}; line-height:1; flex:none; margin-left:1rem;">'
        '<span>&#8212;</span><span>&#9632;</span><span>&#10006;</span></div></div>'
    )


@contextmanager
def ventana_grafico(puntos):
    """Marco de "ventana" liviano alrededor de un gráfico y su pie. Uso:
        with ventana_grafico([color]):
            st.plotly_chart(...)
            st.caption(...)
    """
    with st.container(border=True):
        st.markdown(barra_ventana(puntos, liviana=True), unsafe_allow_html=True)
        yield


def cita(parrafos, fuente):
    """Cita de cierre de un panel: texto centrado en cursiva y la fuente debajo, en gris.
    `parrafos`: lista de párrafos textuales (se muestran entre comillas, sin modificarlos);
    `fuente`: referencia al informe y página."""
    cuerpo = "".join(
        f'<p style="font-style:italic; font-size:1.1rem; line-height:1.6; color:#eaeaea; margin:0 0 0.7rem 0;">'
        f'{"“" if i == 0 else ""}{html.escape(p, quote=False)}{"”" if i == len(parrafos) - 1 else ""}</p>'
        for i, p in enumerate(parrafos)
    )
    st.markdown(
        una_linea(
            '<div style="text-align:center; max-width:46rem; margin:2.5rem auto 1rem auto;">'
            f'{cuerpo}'
            f'<p style="font-size:0.85rem; font-weight:600; color:{GRIS}; margin:0.8rem 0 0 0;">- {html.escape(fuente, quote=False)}</p>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )