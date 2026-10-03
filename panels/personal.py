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

from panels import mini_encuesta
from colors import ROJO_AMENAZA
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
    st.caption("Fuente: UFECI, informes de gestión anuales. Ver fuente exacta por dato en la tabla de metodología.")

    # --- Callout: salto pre/post-pandemia (periodo fiscal, no calendario) ---
    # Estos dos valores NO pertenecen a la serie de arriba: son período fiscal
    # abr-mar, no año calendario. Se muestran aparte para no falsear la tendencia.
    st.subheader("El salto de la pandemia (período fiscal abr-mar)")
    fiscal_pre = datos[datos["periodo"] == "2019-2020"]["valor"].values
    fiscal_post = datos[datos["periodo"] == "2020-2021"]["valor"].values

    if len(fiscal_pre) and len(fiscal_post):
        variacion = (fiscal_post[0] - fiscal_pre[0]) / fiscal_pre[0] * 100
        valor_pre = f"{int(fiscal_pre[0]):,}".replace(",", ".")
        valor_post = f"{int(fiscal_post[0]):,}".replace(",", ".")

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display:flex; align-items:center; justify-content:center; gap:2.5rem; padding:0.5rem 0; flex-wrap:wrap;">
                    <div style="text-align:center;">
                        <div style="font-size:0.9rem; opacity:0.7;">Abr 2019 - Mar 2020</div>
                        <div style="font-size:2.6rem; font-weight:700; font-family:'Space Grotesk',sans-serif;">{valor_pre}</div>
                        <div style="font-size:0.95rem; visibility:hidden;">placeholder</div>
                    </div>
                    <div style="font-size:2rem; opacity:0.5;">→</div>
                    <div style="text-align:center;">
                        <div style="font-size:0.9rem; opacity:0.7;">Abr 2020 - Mar 2021</div>
                        <div style="font-size:2.6rem; font-weight:700; font-family:'Space Grotesk',sans-serif;">{valor_post}</div>
                        <div style="color:#3dd68c; font-size:0.95rem;">↑ +{variacion:.0f}%</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.caption("Período fiscal (abril a marzo), distinto del año calendario del gráfico anterior. Fuente: UFECI, Informe de gestión 2020 (ed. 2021).")

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
                    f"% del total de reportes a UFECI (n = {_fmt_n(total_reportes)})",
                ),
                width="stretch",
            )
            st.caption(
                f"Fuente: UFECI, Informe de gestión 2024-2025. Porcentaje sobre el total de {_fmt_n(total_reportes)} "
                "reportes de 2024. \"Otras modalidades\" se calcula como el resto hasta el total; no es una categoría publicada."
            )

        st.markdown(f"**Dentro de los accesos ilegítimos (n = {_fmt_n(total_accesos)}): ¿qué cuentas vulneran?**")
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
                _barras_horizontales(
                    pd.DataFrame(filas),
                    f"Plataformas más afectadas por accesos ilegítimos ({ANIO_MODALIDADES})",
                    f"% de los accesos ilegítimos (n = {_fmt_n(total_accesos)})",
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