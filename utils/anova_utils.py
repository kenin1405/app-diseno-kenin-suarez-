"""Utilidades para analizar un diseño completamente al azar de un factor."""

import warnings
from os import PathLike
from pathlib import Path
from typing import Any, IO

import pandas as pd
from scipy.stats import studentized_range
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.regression.linear_model import RegressionResultsWrapper


def cargar_datos(archivo: str | PathLike[str] | IO[Any]) -> pd.DataFrame:
    """Carga datos desde un archivo CSV o Excel.

    Args:
        archivo: Ruta del archivo o objeto de archivo con un nombre que incluya
            la extensión.

    Returns:
        Un DataFrame con los datos del archivo.

    Raises:
        ValueError: Si la extensión no corresponde a CSV o XLSX.
    """
    # Paso 1: identificar la extensión desde la ruta o el nombre del archivo.
    nombre = archivo if isinstance(archivo, (str, PathLike)) else getattr(archivo, "name", "")
    extension = Path(nombre).suffix.lower() if nombre else ""

    # Paso 2: leer Excel directamente o dejar que pandas detecte , o ; en CSV.
    if extension == ".xlsx":
        return pd.read_excel(archivo)
    if extension in ("", ".csv"):
        return pd.read_csv(archivo, sep=None, engine="python")
    raise ValueError("Formato no compatible. Use un archivo CSV o XLSX.")


def validar_dca(df: pd.DataFrame, col_trat: str, col_resp: str) -> list[str]:
    """Valida las columnas y replicaciones requeridas para un DCA.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna de tratamientos.
        col_resp: Nombre de la columna de respuesta numérica.

    Returns:
        Lista de errores en español; queda vacía si los datos son válidos.
    """
    errores: list[str] = []

    # Paso 1: comprobar que las columnas existan y tengan funciones distintas.
    faltantes = [col for col in (col_trat, col_resp) if col not in df.columns]
    if faltantes:
        errores.append(f"Faltan las columnas requeridas: {', '.join(faltantes)}.")
        return errores
    if col_trat == col_resp:
        errores.append("La columna de tratamiento y la de respuesta deben ser distintas.")
        return errores

    # Paso 2: revisar datos faltantes y que la respuesta pueda convertirse a números.
    datos = df[[col_trat, col_resp]]
    if datos.isna().any().any():
        errores.append("Hay datos faltantes en las columnas de tratamiento o respuesta.")
    respuesta = pd.to_numeric(df[col_resp], errors="coerce")
    if respuesta.isna().sum() > df[col_resp].isna().sum():
        errores.append("La columna de respuesta debe contener solo valores numéricos.")

    # Paso 3: comprobar el número de tratamientos y de réplicas por tratamiento.
    tratamientos = df[col_trat].nunique(dropna=True)
    if tratamientos < 2:
        errores.append("Se requieren al menos dos tratamientos.")
    replicas = df.groupby(col_trat, dropna=True).size()
    pocos = replicas[replicas < 2].index.tolist()
    if pocos:
        errores.append(
            "Cada tratamiento debe tener al menos dos réplicas. "
            f"Tratamientos con menos de dos: {pocos}."
        )
    return errores


def ajustar_dca(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> RegressionResultsWrapper:
    """Ajusta un modelo lineal para un DCA de un factor.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna de tratamientos.
        col_resp: Nombre de la columna de respuesta.

    Returns:
        El modelo OLS ajustado.

    Raises:
        ValueError: Si los datos no cumplen las condiciones básicas del DCA.
    """
    # Paso 1: detener el ajuste si la validación encuentra problemas.
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError(" ".join(errores))

    # Paso 2: proteger nombres arbitrarios con Q() y ajustar Y = media + tratamiento + error.
    formula = f"Q({col_resp!r}) ~ C(Q({col_trat!r}))"
    return ols(formula, data=df).fit()


def tabla_anova(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Construye la tabla ANOVA tipo II para el modelo ajustado.

    Args:
        modelo: Modelo OLS ajustado por ``ajustar_dca``.

    Returns:
        Tabla con filas Tratamientos, Error y Total y columnas en español.
    """
    # Paso 1: obtener las sumas de cuadrados y grados de libertad tipo II.
    anova = anova_lm(modelo, typ=2)
    fila_trat = anova.loc[anova.index != "Residual"].iloc[0]
    fila_error = anova.loc["Residual"]

    # Paso 2: calcular cuadrados medios (CM = SC / gl) y sumar para el total.
    gl_total = float(fila_trat["df"] + fila_error["df"])
    sc_total = float(fila_trat["sum_sq"] + fila_error["sum_sq"])
    filas = [
        {
            "Fuente": "Tratamientos",
            "gl": float(fila_trat["df"]),
            "SC": float(fila_trat["sum_sq"]),
            "CM": float(fila_trat["sum_sq"] / fila_trat["df"]),
            "F": float(fila_trat["F"]),
            "p-valor": float(fila_trat["PR(>F)"]),
        },
        {
            "Fuente": "Error",
            "gl": float(fila_error["df"]),
            "SC": float(fila_error["sum_sq"]),
            "CM": float(fila_error["sum_sq"] / fila_error["df"]),
            "F": float("nan"),
            "p-valor": float("nan"),
        },
        {
            "Fuente": "Total",
            "gl": gl_total,
            "SC": sc_total,
            "CM": sc_total / gl_total,
            "F": float("nan"),
            "p-valor": float("nan"),
        },
    ]
    return pd.DataFrame(filas, columns=["Fuente", "gl", "SC", "CM", "F", "p-valor"])


def resumen_tratamientos(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> pd.DataFrame:
    """Resume el número de observaciones y la respuesta por tratamiento.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna de tratamientos.
        col_resp: Nombre de la columna de respuesta.

    Returns:
        DataFrame con n, total, media y desviación estándar para cada tratamiento.

    Raises:
        ValueError: Si los datos no cumplen las condiciones básicas del DCA.
    """
    # Paso 1: comprobar la estructura del DCA y convertir la respuesta a numérica.
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError(" ".join(errores))
    datos = df[[col_trat, col_resp]].copy()
    datos[col_resp] = pd.to_numeric(datos[col_resp])

    # Paso 2: calcular n, total, media y s = sqrt(sum((y - media)^2) / (n - 1)).
    resumen = (
        datos.groupby(col_trat)[col_resp]
        .agg(n="count", total="sum", media="mean", desviacion_estandar="std")
        .reset_index()
    )
    return resumen.rename(columns={"desviacion_estandar": "desviación estándar"})


def coeficiente_variacion(
    modelo: RegressionResultsWrapper, df: pd.DataFrame, col_resp: str
) -> float:
    """Calcula el coeficiente de variación del experimento.

    Args:
        modelo: Modelo OLS ajustado.
        df: Datos del experimento.
        col_resp: Nombre de la columna de respuesta.

    Returns:
        Coeficiente de variación porcentual.

    Raises:
        ValueError: Si la media general es cero o la respuesta no es numérica.
    """
    # Paso 1: convertir la respuesta y obtener la media general.
    respuesta = pd.to_numeric(df[col_resp], errors="raise")
    media_general = float(respuesta.mean())
    if media_general == 0:
        raise ValueError("El coeficiente de variación no está definido si la media es cero.")

    # Paso 2: aplicar CV = sqrt(CME) / media general * 100.
    return float((modelo.mse_resid**0.5) / media_general * 100)


def tukey(
    df: pd.DataFrame, col_trat: str, col_resp: str, alfa: float = 0.05
) -> tuple[pd.DataFrame, float]:
    """Calcula comparaciones de Tukey y una DMS para el DCA.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna de tratamientos.
        col_resp: Nombre de la columna de respuesta.
        alfa: Nivel de significancia entre 0 y 1.

    Returns:
        Tupla con la tabla de comparaciones de Tukey y la DMS.

    Raises:
        ValueError: Si los datos no son válidos o alfa no está entre 0 y 1.
    """
    # Paso 1: validar alfa y ajustar el modelo que proporciona el CME y gl del error.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1.")
    modelo = ajustar_dca(df, col_trat, col_resp)
    respuesta = pd.to_numeric(df[col_resp])
    comparaciones = pairwise_tukeyhsd(respuesta, df[col_trat], alpha=alfa)

    # Paso 2: traducir la salida de Tukey a encabezados en español.
    datos = comparaciones.summary().data
    tabla = pd.DataFrame(datos[1:], columns=datos[0]).rename(
        columns={
            "group1": "Tratamiento 1",
            "group2": "Tratamiento 2",
            "meandiff": "Diferencia de medias",
            "p-adj": "p-valor ajustado",
            "lower": "Límite inferior",
            "upper": "Límite superior",
            "reject": "Rechaza H0",
        }
    )

    # Paso 3: usar r común; para desequilibrio, aproximarlo con la media armónica.
    replicas = df.groupby(col_trat).size().astype(float)
    balanceado = replicas.nunique() == 1
    if not balanceado:
        warnings.warn(
            "El diseño no está balanceado; la DMS calculada es aproximada.",
            RuntimeWarning,
            stacklevel=2,
        )
    r = float(replicas.iloc[0]) if balanceado else float(len(replicas) / (1 / replicas).sum())
    tratamientos = int(replicas.size)
    gl_error = float(modelo.df_resid)
    cme = float(modelo.mse_resid)
    q_critico = float(studentized_range.ppf(1 - alfa, tratamientos, gl_error))

    # Paso 4: calcular DMS = q(1 - alfa; tratamientos; glE) * sqrt(CME / r).
    dms = q_critico * (cme / r) ** 0.5
    return tabla, float(dms)


def interpretar_dca(tabla: pd.DataFrame, alfa: float = 0.05) -> str:
    """Interpreta la prueba F de tratamientos en la tabla ANOVA.

    Args:
        tabla: Tabla ANOVA con las columnas ``Fuente`` y ``p-valor``.
        alfa: Nivel de significancia de la prueba.

    Returns:
        Interpretación sencilla de la decisión sobre la hipótesis nula.

    Raises:
        ValueError: Si la tabla no contiene el resultado de Tratamientos.
    """
    # Paso 1: ubicar el p-valor de tratamientos y comparar p con alfa.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1.")
    if "Fuente" not in tabla.columns or "p-valor" not in tabla.columns:
        raise ValueError("La tabla debe incluir las columnas 'Fuente' y 'p-valor'.")
    tratamientos = tabla.loc[tabla["Fuente"] == "Tratamientos", "p-valor"]
    if tratamientos.empty or pd.isna(tratamientos.iloc[0]):
        raise ValueError("La tabla no contiene un p-valor válido para Tratamientos.")

    # Paso 2: H0 establece igualdad de medias; decidir si p <= alfa.
    p_valor = float(tratamientos.iloc[0])
    if p_valor <= alfa:
        return (
            f"Se rechaza H₀ (p = {p_valor:.4g} ≤ α = {alfa:g}). "
            "Hay evidencia de diferencias entre las medias de los tratamientos; "
            "la decisión puede considerar qué tratamientos difieren."
        )
    return (
        f"No se rechaza H₀ (p = {p_valor:.4g} > α = {alfa:g}). "
        "No hay evidencia suficiente de diferencias entre las medias; "
        "no se concluye que algún tratamiento sea distinto."
    )
