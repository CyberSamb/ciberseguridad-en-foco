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
import plotly.graph_objects as go

from etiquetas import etiqueta_legible
from colors import ROJO_AMENAZA, FONDO_OSCURO
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


def _fmt_n(n):
    """Número entero con punto como separador de miles (formato argentino)."""
    return f"{int(round(n)):,}".replace(",", ".")


def _total_anual(datos, anio):
    """Total de incidentes reportados al Estado en un año; None si no está publicado."""
    f = datos[(datos["metrica"] == "incidentes_totales_estado") & (datos["periodo_año"] == anio)]
    return float(f["valor"].iloc[0]) if len(f) else None


def _pie_de_grafico(datos, subset, anio, nota="", chequear_suma=False):
    """Caption común: fuente, total de incidentes del año y aclaración sobre cómo se relacionan las barras."""
    fuente = subset["fuente"].iloc[0] if len(subset) else ""
    total = _total_anual(datos, anio)
    texto = f"Fuente: {fuente}."
    if total is not None:
        texto += f" Total de incidentes reportados en {anio}: {_fmt_n(total)}."
        if chequear_suma and subset["valor"].sum() == total:
            texto += " Las categorías suman el total del año."
    if nota:
        texto += f" {nota}"
    st.caption(texto)


# Severidad: del más grave (rojo oscuro) al menos grave (rojo claro), para que el tono comunique el nivel.
SEVERIDAD_ORDEN = [
    ("incidentes_severidad_critica", "Crítica", "#8B1A1A"),
    ("incidentes_severidad_alta", "Alta", "#d94f4f"),
    ("incidentes_severidad_media", "Media", "#e88a8a"),
    ("incidentes_severidad_baja", "Baja", "#f5c6c6"),
]


def _selector_y_dona_severidad(datos, key):
    """Dona de severidad para el año elegido, con un tono de rojo por nivel."""
    metricas = [m for m, _, _ in SEVERIDAD_ORDEN]
    subset_metricas = datos[datos["metrica"].isin(metricas)]
    anios = sorted(subset_metricas["periodo_año"].unique(), reverse=True)
    if len(anios) == 0:
        return

    anio_elegido = st.selectbox("Año", anios, key=key)
    subset = subset_metricas[subset_metricas["periodo_año"] == anio_elegido]
    valores = {r["metrica"]: float(r["valor"]) for _, r in subset.iterrows()}

    fig = go.Figure(go.Pie(
        labels=[nombre for _, nombre, _ in SEVERIDAD_ORDEN],
        values=[valores.get(m, 0) for m, _, _ in SEVERIDAD_ORDEN],
        sort=False,
        direction="clockwise",
        hole=0.57,
        marker=dict(
            colors=[color for _, _, color in SEVERIDAD_ORDEN],
            line=dict(color=FONDO_OSCURO, width=4),  # separación entre porciones
        ),
        texttemplate="%{value}<br>(%{percent})",
        textposition="auto",
        textfont=dict(size=14),
        hovertemplate="Severidad %{label}<br>%{value} incidentes (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"Incidentes por nivel de severidad — {anio_elegido}", x=0, xanchor="left", y=0.97),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="center", x=0.5),
        margin=dict(t=110, b=20),
        height=480,
        annotations=[dict(
            text=f"<b>{_fmt_n(sum(valores.values()))}</b><br>incidentes",
            x=0.5, y=0.5, showarrow=False, font=dict(size=18),
        )],
    )
    st.plotly_chart(fig, width="stretch")
    _pie_de_grafico(datos, subset, anio_elegido, chequear_suma=True)


# Sector: etiqueta corta y tono de rojo por categoría. Las categorías NO son las mismas todos los años.
# El orden importa: define el orden de los grupos en el eje X multinivel (2022 queda con
# "Críticos del sector Estado" primero y Finanzas después; 2023-2025 con Finanzas y Organismos).
SECTOR_CATEGORIAS = {
    "incidentes_criticos_sector_estado": ("Críticos del sector Estado", "#f5c6c6"),
    "incidentes_sector_finanzas": ("Finanzas", "#d94f4f"),
    "incidentes_sector_estado_gob": ("Organismos de gobierno", "#8B1A1A"),
}


def _grafico_sector(datos):
    """Barras verticales con todos los años: en el eje X, cada año con las categorías sectoriales que publicó."""
    filas = datos[datos["metrica"].isin(SECTOR_CATEGORIAS)].sort_values("periodo_año")
    if filas.empty:
        return

    fig = go.Figure()
    for metrica, (nombre, color) in SECTOR_CATEGORIAS.items():
        sub = filas[filas["metrica"] == metrica]
        if sub.empty:
            continue
        anios = [str(int(a)) for a in sub["periodo_año"]]
        valores = [float(v) for v in sub["valor"]]
        totales = [_total_anual(datos, int(a)) for a in sub["periodo_año"]]
        detalle = [
            f"{_fmt_n(v)} incidentes ({v / t * 100:.0f}% del total de {_fmt_n(t)})" if t else f"{_fmt_n(v)} incidentes"
            for v, t in zip(valores, totales)
        ]
        fig.add_trace(go.Bar(
            name=nombre,
            x=[anios, [nombre] * len(anios)],  # eje multinivel: año > categoría sectorial
            y=valores,
            marker_color=color,
            text=[_fmt_n(v) for v in valores],
            textposition="outside",
            cliponaxis=False,
            customdata=detalle,
            hovertemplate="%{x}<br>%{customdata}<extra></extra>",
        ))
    fig.update_layout(
        title="Incidentes por sector, por año",
        barmode="overlay",  # cada posición del eje X tiene una sola barra
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="center", x=0.5),
        margin=dict(t=110),
    )
    fig.update_xaxes(type="multicategory", title_text="Año y categoría sectorial")
    fig.update_yaxes(title_text="Cantidad de incidentes")
    st.plotly_chart(fig, width="stretch")

    totales_txt = " · ".join(
        f"{int(a)}: {_fmt_n(t)}"
        for a in sorted(filas["periodo_año"].unique())
        if (t := _total_anual(datos, int(a))) is not None
    )
    st.caption(
        "Fuente: CERT.ar, informes anuales de gestión de incidentes. "
        f"Total de incidentes reportados cada año — {totales_txt}. "
        "Las categorías sectoriales cambian entre informes: 2022 publica \"Críticos del sector Estado\" y Finanzas; "
        "2023-2025 publican Finanzas y Organismos de gobierno. \"Críticos del sector Estado\" y \"Organismos de gobierno\" "
        "no son necesariamente equivalentes y no deben compararse entre sí. Cada barra es un subconjunto del total anual."
    )


def _selector_y_barras(datos, metricas, titulo_base, key, nota="", chequear_suma=False):
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
    _pie_de_grafico(datos, subset, anio_elegido, nota, chequear_suma)


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
    total_rango = serie["valor"].sum()
    st.caption(
        f"Total acumulado {rango[0]}-{rango[1]}: {_fmt_n(total_rango)} incidentes reportados. "
        "Fuente: CERT.ar, informes anuales de gestión de incidentes. "
        "El equipo CERT.ar actual fue creado en 2021 (Disposición Administrativa 1/2021), "
        "por lo que el dato 2020 puede no ser comparable con los años siguientes."
    )

    # --- Gráfico 2: desglose por sector (dimensión propia) ---
    st.subheader("Desglose por sector")
    _grafico_sector(datos)

    # --- Gráfico 3: desglose por severidad (dimensión distinta, no comparable con sector) ---
    st.subheader("Desglose por severidad")
    st.caption("Disponible solo para los años en que CERT.ar publicó esta clasificación (2023-2025).")
    _selector_y_dona_severidad(datos, key="severidad")

    # --- Gráfico 4: desglose por tipo de incidente (otra dimensión más) ---
    st.subheader("Desglose por tipo de incidente")
    st.caption("Disponible para 2023-2025. El desglose de 2025 es parcial: el informe original solo publicó el número exacto de dos categorías (Fraude e Intrusión).")
    _selector_y_barras(
        datos, METRICAS_TIPO, "Incidentes por tipo", key="tipo",
        nota="Algunos tipos se publican además como subtipos de otros (por ejemplo, Phishing dentro de Fraude), por lo que las barras no suman el total.",
    )

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