"""
streamlit_app.py
Punto de entrada de la app. Maneja solo la navegación entre los 2 niveles
(Personal / Gubernamental) y delega el contenido de cada
panel a su propia función. Los gráficos reales se agregan en la etapa 4.
"""

import streamlit as st
from data_loader import cargar_datos, filtrar_por_nivel
from panels import personal as panel_personal_modulo
from panels import gubernamental as panel_gubernamental_modulo
from panels import comparacion
from panels import footer
from estilos import aplicar as aplicar_estilos
from colors import ROJO_AMENAZA, AZUL_DEFENSA

def _una_linea(html: str) -> str:
    """Colapsa un bloque HTML a una sola línea. Markdown trata como código las líneas con 4+
    espacios de sangría, así que el HTML pasado a st.markdown no debe tener sangría ni líneas vacías."""
    return " ".join(linea.strip() for linea in html.splitlines() if linea.strip())


# Configuración general de la página (una sola vez, al principio)
st.set_page_config(
    page_title="Ciberseguridad en foco",
    layout="wide",
)
aplicar_estilos()

# Carga de datos: una sola vez por sesión, no en cada interacción del usuario.
# st.cache_data evita releer el CSV cada vez que alguien toca un filtro.
@st.cache_data
def obtener_dataframe():
    return cargar_datos()

df = obtener_dataframe()


# --- Header del proyecto ---
st.title("Ciberseguridad en foco")
st.markdown('<p class="subtitulo-principal">Un tópico que no podemos ignorar</p>', unsafe_allow_html=True)
st.markdown(
    """
    <p class="descripcion-proyecto">
    La ciberseguridad casi no aparece en la conversación pública, pero atraviesa cada aspecto
    fundamental de nuestra vida. Nuestra identidad, nuestra familia e incluso en nuestro trabajo,
    vivimos expuestos a amenazas digitales que desconocemos. Este proyecto trae a la mesa el tema
    analizando delitos informáticos que recibe la ciudadanía (UFECI) y los incidentes que atiende
    el Estado (CERT.ar). Muestra cómo evolucionó cada uno, qué modalidades aparecen en los reportes
    y cómo se relacionan ambas series. Los números son de todo el país; por eso, al final del panel
    Personal, podés hacer un autodiagnóstico para ubicarte vos y preguntarte... ¿Estoy realmente seguro?
    </p>
    """,
    unsafe_allow_html=True,
)


# --- Navegación entre niveles ---
# Tres botones en la misma página, en vez de la barra lateral, dentro de un
# contenedor con borde para que se lean como un panel de control propio.
# El nivel activo se guarda en session_state para sobrevivir entre clics.
# Cada botón fuerza un st.rerun() inmediato tras el clic, para que la
# corrida siguiente arranque limpia.
if "nivel_activo" not in st.session_state:
    st.session_state.nivel_activo = "Personal"

# Color del botón de navegación según el nivel: rojo (Personal) / azul (Gubernamental).
# El tema de Streamlit define un único color primario (rojo), así que el azul del nivel
# Gubernamental se fuerza con CSS. Va dentro del mismo markdown de la barra de "ventana"
# para no agregar un elemento extra a la página.
AZUL_HOVER = "#2f6fe0"
if st.session_state.nivel_activo == "Gubernamental":
    css_nav = f"""
    <style>
    .st-key-boton_gubernamental button,
    .st-key-boton_gubernamental button:focus {{
        background-color: {AZUL_DEFENSA}; border-color: {AZUL_DEFENSA}; color: #ffffff;
    }}
    .st-key-boton_gubernamental button:hover,
    .st-key-boton_gubernamental button:active {{
        background-color: {AZUL_HOVER}; border-color: {AZUL_HOVER}; color: #ffffff;
    }}
    </style>
    """
else:
    css_nav = f"""
    <style>
    .st-key-boton_gubernamental button:hover {{
        border-color: {AZUL_DEFENSA}; color: {AZUL_DEFENSA};
    }}
    </style>
    """

with st.container(border=True):
    # Barra de "ventana" puramente decorativa: dos puntos (rojo/azul, los colores del proyecto)
    # a la izquierda y los íconos de minimizar, redimensionar y cerrar a la derecha.
    # No son controles: no tienen ninguna función y están ocultos para lectores de pantalla.
    st.markdown(
        _una_linea(css_nav + f"""
        <div aria-hidden="true" style="display:flex; justify-content:space-between; align-items:center;
                    margin:0 0.4rem 0.3rem 0.4rem; user-select:none; pointer-events:none;">
            <div style="display:flex; gap:0.5rem;">
                <span style="width:12px; height:12px; border-radius:50%; background:{ROJO_AMENAZA}; display:inline-block;"></span>
                <span style="width:12px; height:12px; border-radius:50%; background:{AZUL_DEFENSA}; display:inline-block;"></span>
            </div>
            <div style="display:flex; gap:0.9rem; color:#8b8fa3; font-size:0.8rem; line-height:1;">
                <span>&#8212;</span><span>&#9632;</span><span>&#10006;</span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Personal",
            width="stretch",
            type="primary" if st.session_state.nivel_activo == "Personal" else "secondary",
            key="boton_personal",
        ):
            st.session_state.nivel_activo = "Personal"
            st.rerun()

    with col2:
        if st.button(
            "Gubernamental",
            width="stretch",
            type="primary" if st.session_state.nivel_activo == "Gubernamental" else "secondary",
            key="boton_gubernamental",
        ):
            st.session_state.nivel_activo = "Gubernamental"
            st.rerun()

nivel_seleccionado = st.session_state.nivel_activo


# --- Cada nivel tiene su propia función de panel ---
# Por ahora cada una solo muestra los datos filtrados como tabla, para
# confirmar que la navegación y el filtrado funcionan de punta a punta.
# En la etapa 4 esto se reemplaza por los gráficos reales.

def panel_personal(datos):
    panel_personal_modulo.render(datos)


def panel_gubernamental(datos):
    panel_gubernamental_modulo.render(datos)


# Despacho: según lo elegido en el sidebar, filtra y llama al panel correspondiente
if nivel_seleccionado == "Personal":
    panel_personal(filtrar_por_nivel(df, "personal"))
else:
    panel_gubernamental(filtrar_por_nivel(df, "gubernamental"))


# --- Comparación entre niveles: siempre visible ---
comparacion.render(df)


# --- Footer: siempre visible, no depende del panel seleccionado ---
footer.render(df)