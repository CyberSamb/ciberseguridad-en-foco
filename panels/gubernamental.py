"""
panels/gubernamental.py
Panel "Gubernamental": exposición del Estado.
Plotly para la serie principal (hay continuidad real 2020-2025). Los
desgloses (sector y severidad) son dimensiones DISTINTAS entre sí -- se
separan en secciones propias para no graficarlas juntas como si fueran
categorías comparables.
"""

import streamlit as st
import plotly.express as px

from etiquetas import etiqueta_legible
from colors import ROJO_AMENAZA
from panels import punchline

# El equipo CERT.ar actual fue creado por la Dirección Nacional de Ciberseguridad
# mediante la Disposición Administrativa 1/2021. Por eso el dato 2020 puede no ser
# comparable con los años siguientes, y la variación del punchline se calcula
# desde este año base (primer año completo con la serie ya consolidada).
ANIO_BASE_PUNCHLINE = 2022

METRICAS_SECTOR = [
    "incidentes_criticos_sector_estado",
    "incidentes_sector_finanzas",
    "incidentes_sector_estado_gob",
]

METRICAS_SEVERIDAD = [
    "incidentes_severidad_alta",
    "incidentes_severidad_critica",
    "incidentes_severidad_media",
    "incidentes_severidad_baja",
]

METRICAS_TIPO = [
    "incidentes_tipo_fraude",
    "incidentes_tipo_compromiso_informacion",
    "incidentes_tipo_contenido_abusivo",
    "incidentes_tipo_intrusion",
    "incidentes_tipo_contenido_danino",
    "incidentes_tipo_disponibilidad",
    "incidentes_tipo_vulnerable",
    "incidentes_tipo_obtencion_informacion",
    "incidentes_tipo_otros",
    "incidentes_tipo_phishing",
    "incidentes_tipo_compromiso_cuenta",
    "incidentes_tipo_modificacion_no_autorizada",
    "incidentes_tipo_acceso_no_autorizado",
]

# Los únicos 6 tipos con dato exacto publicado en los 3 años (2023-2025) --
# se usan como selección por default del gráfico de superposición, ya que
# son los únicos que se pueden leer como tendencia real sin huecos.
METRICAS_TIPO_COMPLETAS = [
    "incidentes_tipo_fraude",
    "incidentes_tipo_phishing",
    "incidentes_tipo_intrusion",
    "incidentes_tipo_modificacion_no_autorizada",
    "incidentes_tipo_acceso_no_autorizado",
    "incidentes_tipo_compromiso_cuenta",
]


def _selector_y_barras(datos, metricas, titulo_base, key):
    """Reutilizada por sector y por severidad: mismo patrón, distinta lista de métricas."""
    subset_metricas = datos[datos["metrica"].isin(metricas)]
    anios = sorted(subset_metricas["periodo_año"].unique(), reverse=True)
    if len(anios) == 0:
        return

    anio_elegido = st.selectbox("Año", anios, key=key)
    subset = subset_metricas[subset_metricas["periodo_año"] == anio_elegido].sort_values("valor")

    fig = px.bar(
        subset,
        x="valor",
        y=subset["metrica"].apply(etiqueta_legible),
        orientation="h",
        title=f"{titulo_base} — {anio_elegido}",
        labels={"x": "Cantidad", "y": ""},
        color_discrete_sequence=[ROJO_AMENAZA],
    )
    fig.update_xaxes(title_text="Cantidad de incidentes")
    fig.update_yaxes(title_text="")
    st.plotly_chart(fig, width="stretch")
    fuente = subset["fuente"].iloc[0] if len(subset) else ""
    st.caption(f"Fuente: {fuente}")


def render(datos):
    st.header("Gubernamental — exposición del Estado")

    # --- Gráfico 1: serie principal, con selector de rango de años ---
    serie_completa = datos[datos["metrica"] == "incidentes_totales_estado"].sort_values("periodo_año")
    anio_min, anio_max = int(serie_completa["periodo_año"].min()), int(serie_completa["periodo_año"].max())

    rango = st.slider(
        "Rango de años a mostrar",
        min_value=anio_min,
        max_value=anio_max,
        value=(anio_min, anio_max),
    )
    serie = serie_completa[
        (serie_completa["periodo_año"] >= rango[0]) & (serie_completa["periodo_año"] <= rango[1])
    ]

    fig1 = px.line(
        serie,
        x="periodo_año",
        y="valor",
        markers=True,
        title="Incidentes de ciberseguridad reportados al Estado argentino",
        labels={"periodo_año": "Año", "valor": "Incidentes reportados"},
        color_discrete_sequence=[ROJO_AMENAZA],
    )
    fig1.update_layout(hovermode="x unified")
    fig1.update_xaxes(tickformat="d", dtick=1, title_text="Año")
    st.plotly_chart(fig1, width="stretch")
    st.caption(
        "Fuente: CERT.ar, informes anuales de gestión de incidentes. "
        "El equipo CERT.ar actual fue creado en 2021 (Disposición Administrativa 1/2021), "
        "por lo que el dato 2020 puede no ser comparable con los años siguientes."
    )

    # --- Gráfico 2: desglose por sector (dimensión propia) ---
    st.subheader("Desglose por sector")
    st.caption("CERT.ar no publica las mismas categorías sectoriales todos los años.")
    _selector_y_barras(datos, METRICAS_SECTOR, "Incidentes por sector", key="sector")

    # --- Gráfico 3: desglose por severidad (dimensión distinta, no comparable con sector) ---
    st.subheader("Desglose por severidad")
    st.caption("Disponible solo para los años en que CERT.ar publicó esta clasificación (2023-2025).")
    _selector_y_barras(datos, METRICAS_SEVERIDAD, "Incidentes por nivel de severidad", key="severidad")

    # --- Gráfico 4: desglose por tipo de incidente (otra dimensión más) ---
    st.subheader("Desglose por tipo de incidente")
    st.caption("Disponible para 2023-2025. El desglose de 2025 es parcial: el informe original solo publicó el número exacto de dos categorías (Fraude e Intrusión).")
    _selector_y_barras(datos, METRICAS_TIPO, "Incidentes por tipo", key="tipo")

    # --- Gráfico 5: superposición de tipos elegidos, como tendencia ---
    # A diferencia del gráfico anterior (un año, todos los tipos), acá se
    # elige uno o más tipos y se ven a lo largo del tiempo. Solo tiene
    # sentido para los tipos con dato en más de un año -- un tipo con un
    # solo punto no traza ninguna línea.
    st.subheader("Comparar la evolución de tipos de incidente")
    tipo_datos = datos[datos["metrica"].isin(METRICAS_TIPO)]
    opciones = sorted(tipo_datos["metrica"].unique(), key=etiqueta_legible)
    default = [m for m in METRICAS_TIPO_COMPLETAS if m in opciones]

    elegidos = st.multiselect(
        "Tipos a comparar",
        options=opciones,
        default=default,
        format_func=etiqueta_legible,
    )

    if elegidos:
        subset = tipo_datos[tipo_datos["metrica"].isin(elegidos)].sort_values("periodo_año")
        fig5 = px.line(
            subset,
            x="periodo_año",
            y="valor",
            color=subset["metrica"].apply(etiqueta_legible),
            markers=True,
            title="Evolución de los tipos de incidente elegidos",
            labels={"periodo_año": "Año", "valor": "Incidentes", "color": "Tipo"},
        )
        fig5.update_layout(hovermode="x unified")
        fig5.update_xaxes(tickformat="d", dtick=1, title_text="Año")
        st.plotly_chart(fig5, width="stretch")
        st.caption(
            "Cada tipo se grafica solo para los años en que el informe original publicó ese dato exacto "
            "-- una línea más corta no significa menos incidentes, significa que ese año no lo desglosaron."
        )
    else:
        st.info("Elegí al menos un tipo para ver su evolución.")

    # --- Punchline: el hallazgo central del panel ---
    # Se calcula desde ANIO_BASE_PUNCHLINE (no desde el primer año de la serie)
    # por la comparabilidad del dato 2020 -- ver comentario al inicio del archivo.
    total = datos[
        (datos["metrica"] == "incidentes_totales_estado")
        & (datos["periodo_año"] >= ANIO_BASE_PUNCHLINE)
    ].sort_values("periodo_año")
    if len(total) >= 2:
        primero = total.iloc[0]
        ultimo = total.iloc[-1]
        variacion = (ultimo["valor"] - primero["valor"]) / primero["valor"] * 100
        punchline.render(
            f"{variacion:+.0f}%",
            f"de variación en los incidentes reportados al Estado argentino entre {int(primero['periodo_año'])} "
            f"y {int(ultimo['periodo_año'])} ({int(primero['valor'])} → {int(ultimo['valor'])} casos).",
        )