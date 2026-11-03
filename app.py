import streamlit as st

AUTOR = "Kenin David Suarez Angel"

st.set_page_config(
    page_title="App de Diseño Experimental",
    page_icon="🌱",
    layout="wide",
)

st.title("App de Diseño Experimental")
st.subheader("Ingeniería Agrícola – Universidad de Sucre")
st.write(
    "El diseño experimental permite planear ensayos de campo de forma ordenada, "
    "comparar tratamientos y obtener conclusiones confiables. Esta app reúne "
    "módulos para apoyar el aprendizaje y la aplicación de estos diseños en "
    "problemas agrícolas."
)

st.header("Módulos")
st.table(
    [
        {
            "Módulo": "DCA — Diseño completamente al azar",
            "Cuándo se usa": "Cuando las unidades experimentales son homogéneas y los tratamientos se asignan al azar.",
            "Ejemplo agrícola": "Comparar cuatro fertilizantes en parcelas uniformes de maíz.",
            "Estado": "Disponible",
        },
        {
            "Módulo": "DBCA — Diseño de bloques completos al azar",
            "Cuándo se usa": "Cuando hay una fuente de variación conocida que se puede controlar agrupando unidades en bloques.",
            "Ejemplo agrícola": "Comparar variedades de arroz en bloques definidos por gradientes del suelo.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DCL — Diseño de cuadrado latino",
            "Cuándo se usa": "Cuando se deben controlar dos fuentes de variación, organizadas en filas y columnas.",
            "Ejemplo agrícola": "Evaluar tratamientos de riego controlando gradientes en dos direcciones del lote.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "DPD — Diseño de parcelas divididas",
            "Cuándo se usa": "Cuando dos factores requieren tamaños de parcela o niveles de aplicación distintos.",
            "Ejemplo agrícola": "Evaluar sistemas de labranza en parcelas grandes y dosis de fertilizante en subparcelas.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "Factoriales",
            "Cuándo se usa": "Cuando se estudian simultáneamente varios factores y sus posibles interacciones.",
            "Ejemplo agrícola": "Evaluar combinaciones de variedades y niveles de fertilización en fríjol.",
            "Estado": "En construcción",
        },
        {
            "Módulo": "RSM — Metodología de superficie de respuesta",
            "Cuándo se usa": "Cuando se busca modelar y optimizar una respuesta en función de factores cuantitativos.",
            "Ejemplo agrícola": "Encontrar la combinación de riego y fertilización que maximiza el rendimiento de tomate.",
            "Estado": "En construcción",
        },
    ]
)

st.header("Instrucciones de uso")
st.markdown(
    """
1. Elige un módulo en el menú lateral.
2. Carga los datos del ensayo cuando el módulo esté disponible.
3. Revisa los resultados y su interpretación.
4. Verifica los supuestos y compara con tu cálculo manual.
"""
)

st.warning(
    "Esta app apoya el aprendizaje. El estudiante interpreta los resultados, "
    "verifica supuestos y compara con su cálculo manual."
)

with st.sidebar:
    st.header("Información del curso")
    st.write(f"**Autor:** {AUTOR}")
    st.write("**Curso:** Diseño Experimental")
    st.write("**Semestre:** 2026-2")
