"""
panels/comparacion.py
Sección transversal: compara la evolución relativa de los dos niveles.
UFECI (reportes de delitos informáticos de la ciudadanía) y CERT.ar (incidentes
gestionados por el Estado) miden cosas distintas y en unidades no comparables,
así que NO se comparan niveles absolutos: ambas series se convierten a un
índice base 100 en un año elegido por el usuario y se comparan solo las
variaciones relativas. Solo se usan los años calendario que tienen las dos series.
"""

import re
import streamlit as st
import plotly.graph_objects as go

from colors import ROJO_AMENAZA, AZUL_DEFENSA
from panels.ventana import ventana_grafico

METRICA_UFECI = "reportes_delitos_informaticos"
METRICA_CERT = "incidentes_totales_estado"


def _serie_calendario(datos, metrica):
    """Serie {año: valor} solo con periodos de año calendario puro ('2021')."""
    filas = datos[
        (datos["metrica"] == metrica)
        & (datos["periodo"].astype(str).apply(lambda p: bool(re.fullmatch(r"\d{4}", p))))
    ]
    return {int(r["periodo_año"]): float(r["valor"]) for _, r in filas.iterrows()}


def render(datos):
    st.markdown("---")
    st.header("Ambos niveles frente a frente")

    ufeci = _serie_calendario(datos, METRICA_UFECI)
    cert = _serie_calendario(datos, METRICA_CERT)
    comunes = sorted(set(ufeci) & set(cert))
    if len(comunes) < 2:
        return

    base = st.radio(
        "Año base (= 100)",
        comunes[:-1],
        index=0,
        horizontal=True,
        key="comparacion_anio_base",
    )
    anios = [a for a in comunes if a >= base]

    fig = go.Figure()
    for nombre, serie, color in [
        ("Ciudadanía: reportes a UFECI", ufeci, ROJO_AMENAZA),
        ("Estado: incidentes en CERT.ar", cert, AZUL_DEFENSA),
    ]:
        indice = [serie[a] / serie[base] * 100 for a in anios]
        fig.add_trace(go.Scatter(
            x=anios,
            y=indice,
            mode="lines+markers",
            name=nombre,
            line=dict(color=color, width=3),
            customdata=[serie[a] for a in anios],
            hovertemplate="%{y:.0f} (valor real: %{customdata:,.0f})<extra>" + nombre + "</extra>",
        ))
    fig.add_hline(y=100, line_dash="dot", line_color="rgba(255,255,255,0.35)")
    fig.update_layout(
        title=f"Evolución relativa (índice, {base} = 100)",
        hovermode="x unified",
        yaxis_title="Índice",
        xaxis_title="Año calendario",
        legend=dict(orientation="h", y=-0.25),
    )
    fig.update_xaxes(tickformat="d", dtick=1)
    with ventana_grafico([ROJO_AMENAZA, AZUL_DEFENSA]):
        st.plotly_chart(fig, width="stretch")

        st.caption(
            "Fuentes: UFECI (Informe 2024, edición 2025) y CERT.ar (informes anuales 2021-2025). "
            "Las unidades no son comparables (denuncias de la ciudadanía vs. incidentes gestionados por "
            "el Estado): solo se compara la variación relativa, no los niveles. El índice depende del año "
            f"base elegido. Se muestran los años calendario con datos en ambas series ({comunes[0]}-{comunes[-1]})."
        )