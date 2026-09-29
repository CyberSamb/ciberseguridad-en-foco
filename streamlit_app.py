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

# Configuración general de la página (una sola vez, al principio)
st.set_page_config(
    page_title="Hablemos de ciberseguridad",
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
st.title("Hablemos de ciberseguridad")
st.markdown('<p class="subtitulo-principal">Un tema fundamental en nuestra vida personal y laboral</p>', unsafe_allow_html=True)
st.markdown(
    """
    <p class="descripcion-proyecto">
    La ciberseguridad casi no aparece en la conversación pública, pero atraviesa nuestra vida
    personal y laboral: cuentas, pagos, trámites, trabajo. Este proyecto la pone sobre la mesa
    con dos fuentes oficiales: los reportes de delitos informáticos que recibe la ciudadanía
    (UFECI) y los incidentes que atiende el Estado (CERT.ar). Muestra cómo evolucionó cada uno,
    qué modalidades aparecen en los reportes y cómo se relacionan ambas series. Los números
    son de todo el país; por eso, al final del panel Personal, podés hacer un autodiagnóstico
    para ubicarte vos. Entonces, la pregunta que debemos hacernos es... ¿Qué tan seguros estamos?
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

with st.container(border=True):
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