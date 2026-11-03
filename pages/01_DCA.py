from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import f as distribucion_f

from utils.anova_utils import (
    ajustar_dca,
    cargar_datos,
    coeficiente_variacion,
    interpretar_dca,
    resumen_tratamientos,
    tabla_anova,
    tukey,
    validar_dca,
)
from utils.diagnostico_utils import (
    grafico_qq,
    grafico_residuos_vs_ajustados,
    prueba_levene,
    prueba_shapiro,
    residuos_y_ajustados,
)


@st.cache_data
def cargar_datos_cache(contenido: bytes, nombre_archivo: str) -> pd.DataFrame:
    """Carga y almacena en caché un CSV o Excel subido o predeterminado."""
    archivo = BytesIO(contenido)
    archivo.name = nombre_archivo
    return cargar_datos(archivo)


st.title("DCA — Diseño completamente al azar")
st.write(
    "El diseño completamente al azar compara tratamientos asignados al azar "
    "a unidades experimentales homogéneas. En este ejemplo se evalúa la "
    "humedad final de yuca (%) en cuatro secadores solares, con cuatro réplicas "
    "por secador."
)

archivo_subido = st.file_uploader(
    "Cargar datos del experimento",
    type=["csv", "xlsx"],
    help="El archivo debe tener una columna de tratamiento y otra de respuesta.",
)

if archivo_subido is None:
    ruta_predeterminada = Path("data/dca_secadores.csv")
    st.caption("No se cargó un archivo; se usan los datos de ejemplo de los cuatro secadores.")
    try:
        contenido_archivo = ruta_predeterminada.read_bytes()
    except OSError as error:
        st.error(f"No se pudo leer el archivo de ejemplo: {error}")
        st.stop()
    nombre_archivo = ruta_predeterminada.name
else:
    contenido_archivo = archivo_subido.getvalue()
    nombre_archivo = archivo_subido.name

try:
    datos = cargar_datos_cache(contenido_archivo, nombre_archivo)
except (OSError, ValueError, ImportError) as error:
    st.error(f"No se pudieron cargar los datos: {error}")
    st.stop()

if datos.empty:
    st.error("El archivo no contiene datos.")
    st.stop()
if len(datos.columns) < 2:
    st.error("El archivo debe contener al menos dos columnas: tratamiento y respuesta.")
    st.stop()

columnas = list(datos.columns)
columnas_categoricas = [
    columna
    for columna in columnas
    if not pd.api.types.is_numeric_dtype(datos[columna])
]
indice_tratamiento = (
    columnas.index(columnas_categoricas[0]) if columnas_categoricas else 0
)

col_trat = st.selectbox(
    "Columna de tratamiento",
    options=columnas,
    index=indice_tratamiento,
)
columnas_respuesta = [columna for columna in columnas if columna != col_trat]
columnas_numericas = [
    columna
    for columna in columnas_respuesta
    if pd.api.types.is_numeric_dtype(datos[columna])
]
indice_respuesta = (
    columnas_respuesta.index(columnas_numericas[-1])
    if columnas_numericas
    else 0
)
col_resp = st.selectbox(
    "Columna de respuesta",
    options=columnas_respuesta,
    index=indice_respuesta,
)
alfa = st.slider(
    "Nivel de significancia (α)",
    min_value=0.01,
    max_value=0.10,
    value=0.05,
    step=0.01,
    format="%.2f",
)

errores = validar_dca(datos, col_trat, col_resp)
if errores:
    for mensaje in errores:
        st.error(mensaje)
    st.stop()

modelo = ajustar_dca(datos, col_trat, col_resp)
anova = tabla_anova(modelo)
resumen = resumen_tratamientos(datos, col_trat, col_resp)
cv = coeficiente_variacion(modelo, datos, col_resp)
p_valor = float(anova.loc[anova["Fuente"] == "Tratamientos", "p-valor"].iloc[0])

pestana_datos, pestana_anova, pestana_comparaciones, pestana_graficos, pestana_supuestos = st.tabs(
    ["Datos", "ANOVA", "Comparaciones", "Gráficos", "Supuestos"]
)

with pestana_datos:
    st.subheader("Datos del experimento")
    st.dataframe(datos, width="stretch", hide_index=True)
    st.subheader("Resumen por tratamiento")
    st.dataframe(
        resumen.style.format(
            {
                "total": "{:.4f}",
                "media": "{:.4f}",
                "desviación estándar": "{:.4f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )

with pestana_anova:
    st.subheader("Análisis de varianza")
    st.dataframe(
        anova.style.format(
            {
                "gl": "{:.0f}",
                "SC": "{:.4f}",
                "CM": "{:.4f}",
                "F": "{:.4f}",
                "p-valor": "{:.4f}",
            },
            na_rep="—",
        ),
        width="stretch",
        hide_index=True,
    )
    gl_tratamientos = float(
        anova.loc[anova["Fuente"] == "Tratamientos", "gl"].iloc[0]
    )
    gl_error = float(anova.loc[anova["Fuente"] == "Error", "gl"].iloc[0])
    f_critica = float(distribucion_f.ppf(1 - alfa, gl_tratamientos, gl_error))
    st.metric("F crítica", f"{f_critica:.4f}")
    st.metric("Coeficiente de variación (CV)", f"{cv:.4f}%")
    if p_valor < alfa:
        st.success(interpretar_dca(anova, alfa))
    else:
        st.info(interpretar_dca(anova, alfa))

with pestana_comparaciones:
    st.subheader("Comparaciones múltiples de Tukey")
    if p_valor < alfa:
        comparaciones, dms = tukey(datos, col_trat, col_resp, alfa)
        if resumen["n"].nunique() > 1:
            st.warning(
                "El diseño no está balanceado; la DMS reportada es aproximada."
            )
        st.dataframe(comparaciones, width="stretch", hide_index=True)
        st.metric("Diferencia mínima significativa (DMS)", f"{dms:.4f}")
    else:
        st.info(
            "No se realiza la prueba de Tukey porque el efecto de tratamientos "
            "no fue significativo en el ANOVA (p-valor ≥ α)."
        )

with pestana_graficos:
    st.subheader("Distribución de la respuesta por tratamiento")
    grafico_cajas = px.box(
        datos,
        x=col_trat,
        y=col_resp,
        points="all",
        labels={col_trat: "Tratamiento", col_resp: "Respuesta"},
    )
    st.plotly_chart(grafico_cajas, width="stretch")

    st.subheader("Media por tratamiento")
    grafico_medias = px.bar(
        resumen,
        x=col_trat,
        y="media",
        error_y="desviación estándar",
        labels={col_trat: "Tratamiento", "media": "Media de la respuesta"},
    )
    st.plotly_chart(grafico_medias, width="stretch")

with pestana_supuestos:
    residuos_ajustados = residuos_y_ajustados(modelo)
    shapiro_estadistico, shapiro_p, shapiro_conclusion = prueba_shapiro(
        residuos_ajustados["Residuos"], alfa
    )
    levene_estadistico, levene_p, levene_conclusion = prueba_levene(
        datos, col_trat, col_resp, alfa
    )

    st.subheader("Gráficas de diagnóstico")
    st.plotly_chart(
        grafico_residuos_vs_ajustados(residuos_ajustados),
        width="stretch",
    )
    st.plotly_chart(grafico_qq(residuos_ajustados["Residuos"]), width="stretch")

    st.subheader("Pruebas de supuestos")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Prueba": "Shapiro-Wilk",
                    "Estadístico": shapiro_estadistico,
                    "p-valor": shapiro_p,
                    "Conclusión": shapiro_conclusion,
                },
                {
                    "Prueba": "Levene (mediana)",
                    "Estadístico": levene_estadistico,
                    "p-valor": levene_p,
                    "Conclusión": levene_conclusion,
                },
            ]
        ).style.format(
            {"Estadístico": "{:.4f}", "p-valor": "{:.4f}"}
        ),
        width="stretch",
        hide_index=True,
    )

    st.markdown(
        """
**Normalidad:** Shapiro-Wilk evalúa si los residuos son compatibles con una
distribución normal. El gráfico Q-Q permite comparar sus cuantiles con los
cuantiles teóricos normales; el gráfico de residuos frente a ajustados también
ayuda a detectar patrones.

**Homogeneidad de varianzas:** Levene, centrada en la mediana, evalúa si la
variabilidad de la respuesta es similar entre tratamientos.

**Independencia:** No se determina con estas pruebas. En un DCA se sustenta en
la asignación aleatoria de tratamientos y en que las unidades experimentales
sean independientes; debe revisarse cómo se ejecutó el ensayo.
"""
    )
