"""
panels/mini_encuesta.py
Mini-encuesta de autodiagnóstico: 10 preguntas de hábitos de seguridad
personal, 5 niveles de resultado según el puntaje. No guarda ninguna
respuesta en ningún lado -- es un espejo personal para que el usuario se
ubique, no una encuesta real ni una fuente de datos.

Nota: en "reutilizás la misma contraseña", el punto se otorga al responder
"No" (reutilizar es el hábito inseguro) -- es la única pregunta invertida
respecto a la regla general de "Sí = punto", para que el puntaje total sea
lógicamente consistente con seguridad real.
"""

import streamlit as st

from colors import ROJO_AMENAZA
from panels.ventana import barra_ventana

# (pregunta, opciones, la opción que otorga el punto)
PREGUNTAS = [
    ("¿Utilizás gestor de contraseñas?", ["No", "Sí", "No sé lo que es"], "Sí"),
    ("¿Utilizás doble factor de autenticación?", ["No", "Sí", "No sé lo que es"], "Sí"),
    ("¿Tus contraseñas tienen 12 caracteres o más?", ["No", "Sí"], "Sí"),
    ("¿Tus contraseñas combinan letras, números y símbolos (por ejemplo: a-z, A-Z, 0-9, &, #, $)?", ["No", "Sí"], "Sí"),
    ("¿Sabrías responder ante una vulneración de tus datos?", ["No", "Sí"], "Sí"),
    ("¿Reutilizás la misma contraseña en más de una cuenta?", ["No", "Sí"], "No"),
    ("¿Sabrías diferenciar un correo de phishing de uno verdadero?", ["No", "Sí"], "Sí"),
    ("¿Verificás la autenticidad de un enlace antes de hacer clic?", ["No", "Sí"], "Sí"),
    ("¿Estás al día con las nuevas amenazas que surgen cada semana?", ["No", "Sí"], "Sí"),
    ("¿Te preocupás por tu seguridad digital?", ["No", "Sí"], "Sí"),
]

NIVELES = [
    (10, 10, "¡Super seguro!"),
    (7, 9, "Seguro"),
    (5, 6, "Faltan cosas"),
    (3, 4, "Crítico"),
    (0, 2, "Expuesto"),
]


def _nivel_para(puntaje):
    for minimo, maximo, etiqueta in NIVELES:
        if minimo <= puntaje <= maximo:
            return etiqueta
    return "Expuesto"


def _contenido():
    st.markdown('<h2 class="titulo-gap">Y vos, ¿Estás seguro?</h2>', unsafe_allow_html=True)
    st.markdown("Los números de arriba son de todo el país. Ahora, los tuyos.")
    st.caption(
        "Esto no es una encuesta real ni se almacenan las respuestas, es un autodiagnóstico "
        "rápido para que te ubiques, no un dato poblacional general."
    )

    respuestas = {}
    with st.form("mini_encuesta"):
        for i, (pregunta, opciones, _) in enumerate(PREGUNTAS):
            respuestas[i] = st.radio(pregunta, opciones, key=f"mini_{i}", horizontal=True)
        enviado = st.form_submit_button("Ver mi nivel")

    if not enviado:
        return

    puntaje = sum(
        1 for i, (_, _, opcion_correcta) in enumerate(PREGUNTAS)
        if respuestas[i] == opcion_correcta
    )
    nivel = _nivel_para(puntaje)

    st.markdown(
        f"""
        <div style="text-align:center; padding:1rem;">
            <div style="font-size:1.1rem; opacity:0.75;">Tu nivel de seguridad</div>
            <div style="font-size:2.2rem; font-weight:700; font-family:'Space Grotesk',sans-serif;">{nivel}</div>
            <div style="font-size:1.1rem; opacity:0.8;">{puntaje} / 10</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(datos):
    st.markdown("---")
    with st.container(border=True):
        # Barra de "ventana" decorativa: punto rojo, barra de búsqueda (sin función) y
        # los íconos de minimizar, redimensionar y cerrar.
        st.markdown(barra_ventana([ROJO_AMENAZA], buscador=True), unsafe_allow_html=True)
        _contenido()