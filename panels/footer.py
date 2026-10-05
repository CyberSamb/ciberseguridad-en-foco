"""
panels/footer.py
Footer metodológico: fuentes, limitaciones y declaración de uso de IA.
Se muestra siempre, en los dos niveles, al final de la página.

Las fuentes se extraen directo del CSV (no se tipean a mano) para que el
footer nunca quede desincronizado si el dataset cambia.
"""

import streamlit as st


def render(datos):
    st.markdown("---")

    with st.expander("Fuentes de datos"):
        fuentes = (
            datos[["nivel", "fuente", "url"]]
            .drop_duplicates()
            .sort_values(["nivel", "fuente"])
        )
        for nivel in ["personal", "gubernamental"]:
            st.markdown(f"**{nivel.capitalize()}**")
            subset = fuentes[fuentes["nivel"] == nivel]
            for _, fila in subset.iterrows():
                st.markdown(f"- [{fila['fuente']}]({fila['url']})")

    with st.expander("Limitaciones metodológicas"):
        st.markdown(
            """
            - **UFECI (Personal):** el criterio de conteo cambió de año fiscal (abril-marzo) a año
              calendario entre informes. La serie principal usa solo años calendario (2021-2024);
              los períodos fiscales (2019/20 a 2022/23) se muestran aparte porque usan el corte abril-marzo.
            - **CERT.ar (Gubernamental):** la taxonomía de tipos de incidente se amplió a partir de
              2023; el desglose sectorial no se publicó con los mismos criterios todos los años. En 2021, el
              informe presenta tres valores levemente distintos entre su texto y sus gráficos (sector
              Otros: 124 vs. 125; tipo Configuración errónea: 4 vs. 2; tipo Otros: 1 vs. 2); se usan
              las cifras del texto, que suman el total de 591 incidentes.
              Los tres desgloses (sector, tipo y severidad) suman el total anual de incidentes de
              CERT.ar en cada año de 2021 a 2025.
            - **UFECI (Personal) y CERT.ar (Gubernamental):** miden cosas distintas (reportes de
              delitos informáticos de la ciudadanía vs. incidentes gestionados por el Estado) y no
              deben compararse en niveles absolutos.
            """
        )

    with st.expander("Declaración de uso de Inteligencia Artificial"):
        st.markdown(
            """
            Se utilizó Claude (Anthropic) como herramienta de asistencia bajo supervisión directa
            del autor, en las siguientes etapas:

            - **Recolección y validación de fuentes:** verificación de cifras contra los PDFs
              originales (UFECI, CERT.ar). También se analizaron fuentes que luego se descartaron
              por no ser datos abiertos; no forman parte de la visualización.
            - **Construcción y limpieza del dataset:** estructuración en formato tabular,
              normalización de formatos de fecha, documentación de limitaciones metodológicas.
            - **Desarrollo de la aplicación:** asistencia en la generación de código Python/Streamlit
              (carga de datos, navegación, visualizaciones), revisado y probado en cada paso.

            No se utilizó IA generativa para crear las visualizaciones finales de forma automatizada:
            cada gráfico fue definido, revisado y ajustado por el autor. No se generaron ni
            manipularon imágenes con IA generativa.
            """
        )

    st.caption("Ciberseguridad en foco — Concurso Nacional de Visualización de Datos 2026, Contar con Datos -- por CyberSamb")