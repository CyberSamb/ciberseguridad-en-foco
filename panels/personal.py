"""
panels/personal.py
Panel "Personal": exposición de la ciudadanía.
Usa Plotly porque estos gráficos necesitan interactividad real (hover, zoom)
sobre series temporales.
"""

import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from panels import mini_encuesta
from colors import ROJO_AMENAZA, FONDO_OSCURO
from etiquetas import etiqueta_legible


def _es_anio_calendario_puro(periodo: str) -> bool:
    """True solo para '2021', '2022', etc. -- False para '2019-2020' (fiscal) o '~2021' (aprox)."""
    return bool(re.fullmatch(r"\d{4}", str(periodo)))


def _fmt_n(n):
    """Número entero con punto como separador de miles (formato argentino)."""
    return f"{int(round(n)):,}".replace(",", ".")


def _fmt_pct(v):
    """Porcentaje con una decimal y coma (formato argentino); enteros sin decimal."""
    return f"{v:.1f}".replace(".", ",").replace(",0", "")


def _valor(datos, metrica, anio):
    """Valor de una métrica para un año calendario; None si no existe."""
    f = datos[(datos["metrica"] == metrica) & (datos["periodo_año"] == anio)]
    return float(f["valor"].iloc[0]) if len(f) else None


def _barras_horizontales(df, titulo, titulo_x):
    """Barras horizontales ordenadas, con etiqueta de valor y sin título en el eje Y."""
    df = df.sort_values("pct")
    fig = px.bar(
        df, x="pct", y="etiqueta", orientation="h", title=titulo, text="texto",
        custom_data=["detalle"], color_discrete_sequence=[ROJO_AMENAZA],
    )
    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}<br>%{customdata[0]}<extra></extra>")
    fig.update_xaxes(title_text=titulo_x, ticksuffix="%", range=[0, df["pct"].max() * 1.2])
    fig.update_yaxes(title_text="")
    return fig


# Colores de marca de cada plataforma (excepción deliberada a la paleta de dos colores del
# proyecto: acá el color identifica la aplicación, no el significado amenaza/defensa).
COLORES_PLATAFORMA = {
    "WhatsApp": "#25D366",
    "Mercado Pago": "#00B1EA",
    "Facebook": "#1877F2",
    "Instagram": "#E1306C",
    "Gmail": "#EA4335",
    "Hotmail": "#FFB900",
    "Otras plataformas": "#8A8FA3",
}


def _dona_plataformas(df, titulo, total_accesos):
    """Gráfico de dona: cada porción con el color de su plataforma y el total al centro."""
    fig = go.Figure(go.Pie(
        labels=df["etiqueta"],
        values=df["pct"],
        hole=0.57,
        direction="clockwise",
        marker=dict(
            colors=[COLORES_PLATAFORMA.get(e, "#8A8FA3") for e in df["etiqueta"]],
            line=dict(color=FONDO_OSCURO, width=4),  # separación entre porciones
        ),
        texttemplate="%{value}%",
        textposition="auto",
        textfont=dict(size=14, color="white"),
        hovertemplate="%{label}<br>%{value}% de los accesos ilegítimos<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=titulo, x=0, xanchor="left", y=0.97),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="center", x=0.5),
        margin=dict(t=110, b=20),
        height=480,
        annotations=[dict(
            text=f"<b>{_fmt_n(total_accesos)}</b><br>accesos ilegítimos",
            x=0.5, y=0.5, showarrow=False, font=dict(size=18),
        )],
    )
    return fig


def render(datos):
    st.header("Personal — exposición de la ciudadanía")

    # --- Gráfico 1: serie principal de reportes a UFECI, años calendario ---
    # Se filtra explícitamente a periodos "puros" (ej. "2021") para no mezclar
    # con los periodos fiscales (ej. "2020-2021"), que usan un criterio de
    # corte distinto (abril-marzo) y no son comparables punto a punto.
    serie = datos[
        (datos["metrica"] == "reportes_delitos_informaticos")
        & (datos["periodo"].apply(_es_anio_calendario_puro))
    ].sort_values("periodo_año")

    # Selector de rango de años (mismo patrón que el panel Gubernamental).
    # Se filtra una copia: `serie` completa se conserva para el punchline de abajo,
    # que siempre debe calcularse sobre todo el período 2021-2024.
    anio_min, anio_max = int(serie["periodo_año"].min()), int(serie["periodo_año"].max())
    rango = st.slider(
        "Rango de años a mostrar",
        min_value=anio_min,
        max_value=anio_max,
        value=(anio_min, anio_max),
        key="rango_anios_personal",
    )
    serie_filtrada = serie[
        (serie["periodo_año"] >= rango[0]) & (serie["periodo_año"] <= rango[1])
    ]

    fig1 = px.line(
        serie_filtrada,
        x="periodo_año",
        y="valor",
        markers=True,
        title="Reportes de delitos informáticos recibidos por UFECI (año calendario)",
        labels={"periodo_año": "Año", "valor": "Reportes recibidos"},
        color_discrete_sequence=[ROJO_AMENAZA],
    )
    fig1.update_layout(hovermode="x unified")
    fig1.update_xaxes(tickformat="d", dtick=1, title_text="Año calendario")
    st.plotly_chart(fig1, width="stretch")
    st.caption(
        "Fuente: UFECI, Informe de gestión 2024-2025 (edición de junio de 2025), sección \"Comparación interanual\". Los totales de cada año "
        "(reportes recibidos de enero a diciembre) salen de ese mismo informe, con un único criterio de conteo."
    )

    # --- Callout: períodos fiscales (abr-mar), NO año calendario ---
    # Estos valores NO pertenecen a la serie de arriba: son períodos fiscales de abril a
    # marzo, no años calendario. Se muestran aparte para no falsear la tendencia.
    st.subheader("Períodos fiscales (abril-marzo)")
    fiscales = datos[
        (datos["metrica"] == "reportes_delitos_informaticos")
        & (datos["periodo"].astype(str).str.fullmatch(r"\d{4}-\d{4}"))
    ].sort_values("periodo")

    if len(fiscales) >= 2:
        bloques = []
        valor_previo = None
        for _, fila in fiscales.iterrows():
            inicio, fin = str(fila["periodo"]).split("-")
            valor = float(fila["valor"])
            if valor_previo is None:
                linea_variacion = '<div style="font-size:0.95rem; visibility:hidden;">placeholder</div>'
            else:
                variacion = (valor - valor_previo) / valor_previo * 100
                linea_variacion = f'<div style="color:#3dd68c; font-size:0.95rem;">↑ +{variacion:.0f}%</div>'
                bloques.append('<div style="font-size:2rem; opacity:0.5;">→</div>')
            bloques.append(
                f'''<div style="text-align:center;">
                    <div style="font-size:0.9rem; opacity:0.7;">Abr {inicio} - Mar {fin}</div>
                    <div style="font-size:2.2rem; font-weight:700; font-family:'Space Grotesk',sans-serif;">{_fmt_n(valor)}</div>
                    {linea_variacion}
                </div>'''
            )
            valor_previo = valor

        with st.container(border=True):
            st.markdown(
                f'''<div style="display:flex; align-items:center; justify-content:center; gap:1.6rem; padding:0.5rem 0; flex-wrap:wrap;">{"".join(bloques)}</div>''',
                unsafe_allow_html=True,
            )
        fuentes = " y ".join(sorted(fiscales["fuente"].str.replace("UFECI - ", "", regex=False).unique()))
        st.caption(
            "Períodos fiscales (abril a marzo), distintos del año calendario del gráfico anterior: "
            f"no se comparan punto a punto con él. Fuente: UFECI, {fuentes}."
        )

    # --- Gráfico 2: qué te pueden vulnerar (plataformas más afectadas, 2024) ---
    st.subheader("Qué te pueden vulnerar")
    # Dos gráficos con denominadores DISTINTOS y explícitos (no se pueden sumar entre sí):
    # (1) modalidades como % del total de reportes del año; (2) composición interna de
    # los accesos ilegítimos, que son solo una parte (≈8%) del total.
    ANIO_MODALIDADES = 2024
    total_reportes = _valor(datos, "reportes_delitos_informaticos", ANIO_MODALIDADES)
    total_accesos = _valor(datos, "accesos_ilegitimos_total", ANIO_MODALIDADES)

    if total_reportes and total_accesos:
        st.markdown("**¿Qué tipo de delito se reporta?**")
        modalidades = [
            ("Fraude en línea", _valor(datos, "reportes_modalidad_fraude_en_linea", ANIO_MODALIDADES)),
            ("Usurpación de identidad", _valor(datos, "reportes_modalidad_usurpacion_identidad", ANIO_MODALIDADES)),
            ("Acceso ilegítimo", total_accesos),
            ("Phishing", _valor(datos, "reportes_modalidad_phishing", ANIO_MODALIDADES)),
            ("Acoso", _valor(datos, "reportes_modalidad_acoso", ANIO_MODALIDADES)),
        ]
        if all(v is not None for _, v in modalidades):
            modalidades.append(("Otras modalidades (calculado)", total_reportes - sum(v for _, v in modalidades)))
            filas = [
                {"etiqueta": n, "pct": v / total_reportes * 100,
                 "texto": f"{_fmt_pct(v / total_reportes * 100)}%",
                 "detalle": f"{_fmt_n(v)} de {_fmt_n(total_reportes)} reportes"}
                for n, v in modalidades
            ]
            st.plotly_chart(
                _barras_horizontales(
                    pd.DataFrame(filas),
                    f"Modalidades más reportadas ({ANIO_MODALIDADES})",
                    f"% del total de reportes a UFECI (total: {_fmt_n(total_reportes)} reportes)",
                ),
                width="stretch",
            )
            st.caption(
                f"Fuente: UFECI, Informe de gestión 2024-2025. Porcentaje sobre el total de {_fmt_n(total_reportes)} "
                "reportes de 2024. \"Otras modalidades\" se calcula como el resto hasta el total; no es una categoría publicada. "
                "Se muestra solo 2024 porque es el desglose publicado sobre año calendario completo (enero-diciembre); "
                "los informes anteriores usan períodos fiscales (abril-marzo) y no son comparables."
            )

        st.markdown(f"**Dentro de los accesos ilegítimos (total: {_fmt_n(total_accesos)} accesos): ¿qué cuentas vulneran?**")
        plataformas = [
            ("WhatsApp", "pct_accesos_ilegitimos_whatsapp"),
            ("Mercado Pago", "pct_accesos_ilegitimos_mercadopago"),
            ("Otras plataformas", "pct_accesos_ilegitimos_otras_plataformas"),
            ("Facebook", "pct_accesos_ilegitimos_facebook"),
            ("Gmail", "pct_accesos_ilegitimos_gmail"),
            ("Instagram", "pct_accesos_ilegitimos_instagram"),
            ("Hotmail", "pct_accesos_ilegitimos_hotmail"),
        ]
        filas = []
        for nombre, metrica in plataformas:
            v = _valor(datos, metrica, ANIO_MODALIDADES)
            if v is not None:
                filas.append({"etiqueta": nombre, "pct": v, "texto": f"{_fmt_pct(v)}%",
                              "detalle": f"{_fmt_pct(v)}% de los {_fmt_n(total_accesos)} accesos ilegítimos"})
        if filas:
            st.plotly_chart(
                _dona_plataformas(
                    pd.DataFrame(filas),
                    f"Plataformas más afectadas por accesos ilegítimos ({ANIO_MODALIDADES}): {_fmt_pct(total_accesos / total_reportes * 100)}% de todos los reportes",
                    total_accesos,
                ),
                width="stretch",
            )
            st.caption(
                f"Fuente: UFECI, Informe de gestión 2024-2025. Los accesos ilegítimos son {_fmt_pct(total_accesos / total_reportes * 100)}% "
                "del total de reportes; estos porcentajes se calculan solo sobre ese subconjunto y no se suman con los del gráfico anterior."
            )

    # --- Punchline: crecimiento anual compuesto de reportes UFECI (calendario) ---
    # Se calcula dinámicamente desde la serie calendario, no está hardcodeado.
    if len(serie) >= 2:
        primero, ultimo = serie.iloc[0], serie.iloc[-1]
        anios = int(ultimo["periodo_año"] - primero["periodo_año"])
        if anios > 0 and primero["valor"] > 0:
            cagr = ((ultimo["valor"] / primero["valor"]) ** (1 / anios) - 1) * 100
            v0 = f"{int(primero['valor']):,}".replace(",", ".")
            v1 = f"{int(ultimo['valor']):,}".replace(",", ".")
            st.markdown(
                f"""
                <div style="background-color:#1a1a2e; padding:1.4rem 2rem; border-left:6px solid {ROJO_AMENAZA}; border-radius:4px; max-width:52rem; margin:1rem 0;">
                <span style="font-size:2.5rem; font-weight:bold; color:{ROJO_AMENAZA}; font-family:'Space Grotesk',sans-serif;">+{cagr:.1f}% por año</span><br>
                <span style="color:#eaeaea;">crecieron los reportes de delitos informáticos recibidos por UFECI entre
                {int(primero['periodo_año'])} y {int(ultimo['periodo_año'])} ({v0} → {v1}). Son reportes recibidos,
                no delitos ocurridos: dependen también de cuánta gente denuncia.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    mini_encuesta.render(datos)