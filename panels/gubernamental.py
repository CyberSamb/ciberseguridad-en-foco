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


# Desglose de tipos de incidente al nivel más fino que publica CERT.ar. En los años con dato
# (2021 a 2025) las categorías forman una partición completa: suman el total del año.
TIPO_DETALLE = {
    "incidentes_detalle_phishing": "Phishing",
    "incidentes_detalle_compromiso_cuenta": "Compromiso de cuenta",
    "incidentes_detalle_acceso_no_autorizado": "Acceso no autorizado a la información",
    "incidentes_detalle_modificacion_no_autorizada": "Modificación no autorizada de la información",
    "incidentes_detalle_spam": "SPAM",
    "incidentes_detalle_malware": "Malware",
    "incidentes_detalle_ransomware": "Ransomware",
    "incidentes_detalle_revelacion_informacion": "Revelación de información",
    "incidentes_detalle_configuracion_erronea": "Configuración errónea",
    "incidentes_detalle_sistema_vulnerable": "Sistema vulnerable",
    "incidentes_detalle_explotacion_vulnerabilidades": "Explotación de vulnerabilidades",
    "incidentes_detalle_publicacion_servicios_vulnerables": "Publicación de servicios vulnerables",
    "incidentes_detalle_denegacion_servicio": "Denegación de servicio (DoS/dDoS)",
    "incidentes_detalle_suplantacion": "Suplantación",
    "incidentes_detalle_compromiso_equipo_sistema": "Compromiso de equipo/sistema",
    "incidentes_detalle_escaneo_redes": "Escaneo de redes / análisis de tráfico",
    "incidentes_detalle_apt": "APT",
    "incidentes_detalle_ataque_desconocido": "Ataque desconocido",
    "incidentes_detalle_ataque_fuerza_bruta": "Ataque de fuerza bruta",
    "incidentes_detalle_botnet": "Botnet",
    "incidentes_detalle_robo": "Robo",
    "incidentes_detalle_ingenieria_social": "Ingeniería social",
    "incidentes_detalle_otros": "Otros",
}
METRICAS_TIPO_DETALLE = list(TIPO_DETALLE)
METRICAS_TIPO_DETALLE_DEFAULT = [
    "incidentes_detalle_phishing",
    "incidentes_detalle_compromiso_cuenta",
    "incidentes_detalle_acceso_no_autorizado",
    "incidentes_detalle_modificacion_no_autorizada",
    "incidentes_detalle_spam",
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


# Sectores publicados por CERT.ar (en cada informe figura un subconjunto de ellos, más "Otros").
# El orden define el orden de las barras dentro de cada año; el color es fijo por sector
# para poder seguir un mismo sector a lo largo de los años.
SECTORES = {
    "incidentes_sector_estado": ("Estado", "#d94f4f"),
    "incidentes_sector_finanzas": ("Finanzas", "#3a86ff"),
    "incidentes_sector_otros": ("Otros", "#8A8FA3"),
    "incidentes_sector_salud": ("Salud", "#3dd68c"),
    "incidentes_sector_transportes": ("Transportes", "#f2a65a"),
    "incidentes_sector_tics": ("TICs", "#b07cf0"),
    "incidentes_sector_alimentacion": ("Alimentación", "#e8d44d"),
    "incidentes_sector_energia": ("Energía", "#ff7ab8"),
    "incidentes_sector_hidrico": ("Hídrico", "#4cc9f0"),
    "incidentes_sector_quimico": ("Químico", "#a1887f"),
    "incidentes_sector_espacio": ("Espacio", "#d0d0d0"),
}
METRICAS_SECTOR = list(SECTORES)


def _grafico_sector(datos):
    """Barras verticales con todos los años: cada año agrupa los sectores que publicó CERT.ar."""
    filas = datos[datos["metrica"].isin(SECTORES)].sort_values("periodo_año")
    if filas.empty:
        return

    anios = sorted(int(a) for a in filas["periodo_año"].unique())
    fig = go.Figure()
    for metrica, (nombre, color) in SECTORES.items():
        sub = filas[filas["metrica"] == metrica]
        if sub.empty:
            continue
        xs = [str(int(a)) for a in sub["periodo_año"]]
        ys = [float(v) for v in sub["valor"]]
        totales = [_total_anual(datos, int(a)) for a in sub["periodo_año"]]
        detalle = [
            f"{_fmt_n(v)} incidentes ({v / t * 100:.0f}% del total de {_fmt_n(t)})" if t else f"{_fmt_n(v)} incidentes"
            for v, t in zip(ys, totales)
        ]
        fig.add_trace(go.Bar(
            name=nombre,
            x=xs,
            y=ys,
            marker_color=color,
            text=[_fmt_n(v) if v >= 20 else "" for v in ys],  # etiqueta solo en barras visibles
            textposition="outside",
            cliponaxis=False,
            customdata=detalle,
            hovertemplate=f"{nombre} · %{{x}}<br>%{{customdata}}<extra></extra>",
        ))
    fig.update_layout(
        title="Incidentes por sector, por año",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="center", x=0.5),
        margin=dict(t=110),
        height=520,
    )
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=[str(a) for a in anios], title_text="Año")
    fig.update_yaxes(title_text="Cantidad de incidentes")
    st.plotly_chart(fig, width="stretch")

    totales_txt = " · ".join(
        f"{a}: {_fmt_n(t)}" for a in anios if (t := _total_anual(datos, a)) is not None
    )
    diferencias = [
        f"{a} ({_fmt_n(filas[filas['periodo_año'] == a]['valor'].sum())} sectores vs. {_fmt_n(t)} total)"
        for a in anios
        if (t := _total_anual(datos, a)) is not None and filas[filas["periodo_año"] == a]["valor"].sum() != t
    ]
    nota_dif = (
        " En " + ", ".join(diferencias) + " la suma de los sectores publicados difiere del total anual."
        if diferencias else ""
    )
    st.caption(
        "Fuente: CERT.ar, informes anuales de gestión de incidentes. "
        f"Total de incidentes reportados cada año — {totales_txt}. "
        "Cada informe publica los sectores que registró ese año (\"Otros\" es una categoría del propio informe), "
        f"por eso no todos los sectores aparecen en todos los años.{nota_dif}"
    )


def _selector_y_barras(datos, metricas, titulo_base, key, nota="", chequear_suma=False, etiquetas=None):
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
        y=subset["metrica"].apply(lambda m: etiquetas.get(m, m) if etiquetas else etiqueta_legible(m)),
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
    st.caption("Disponible para 2021 a 2025.")
    _selector_y_dona_severidad(datos, key="severidad")

    # --- Gráfico 4: desglose por tipo de incidente (otra dimensión más) ---
    st.subheader("Desglose por tipo de incidente")
    st.caption(
        "Tipos de incidente publicados por CERT.ar al nivel más detallado. Disponible para 2021 a 2025. "
        "La taxonomía cambia entre años (por ejemplo, Malware aparece en 2021-2023 y Ransomware en 2024-2025)."
    )
    _selector_y_barras(
        datos, METRICAS_TIPO_DETALLE, "Incidentes por tipo", key="tipo",
        chequear_suma=True, etiquetas=TIPO_DETALLE,
    )

    # --- Gráfico 5: superposición de tipos elegidos, como tendencia ---
    # A diferencia del gráfico anterior (un año, todos los tipos), acá se
    # elige uno o más tipos y se ven a lo largo del tiempo. Solo tiene
    # sentido para los tipos con dato en más de un año -- un tipo con un
    # solo punto no traza ninguna línea.
    st.subheader("Comparar la evolución de tipos de incidente")
    tipo_datos = datos[datos["metrica"].isin(METRICAS_TIPO_DETALLE)]
    opciones = sorted(tipo_datos["metrica"].unique(), key=lambda m: TIPO_DETALLE[m])
    default = [m for m in METRICAS_TIPO_DETALLE_DEFAULT if m in opciones]

    elegidos = st.multiselect(
        "Tipos a comparar",
        options=opciones,
        default=default,
        format_func=lambda m: TIPO_DETALLE[m],
    )

    if elegidos:
        subset = tipo_datos[tipo_datos["metrica"].isin(elegidos)].sort_values("periodo_año")
        fig5 = px.line(
            subset,
            x="periodo_año",
            y="valor",
            color=subset["metrica"].map(TIPO_DETALLE),
            markers=True,
            title="Evolución de los tipos de incidente elegidos",
            labels={"periodo_año": "Año", "valor": "Incidentes", "color": "Tipo"},
        )
        fig5.update_layout(hovermode="x unified")
        fig5.update_xaxes(tickformat="d", dtick=1, title_text="Año")
        st.plotly_chart(fig5, width="stretch")
        st.caption(
            "Se grafican los años 2021 a 2025, todos con desglose completo: un tipo que no figura en un año "
            "suma 0 incidentes en ese informe. La taxonomía cambia entre años, por lo que algunas líneas son cortas."
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