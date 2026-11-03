"""Utilidades para revisar supuestos de un diseño completamente al azar."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import levene, probplot, shapiro
from statsmodels.regression.linear_model import RegressionResultsWrapper


def residuos_y_ajustados(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Obtiene los residuos y valores ajustados de un modelo.

    Args:
        modelo: Modelo lineal ajustado.

    Returns:
        DataFrame con las columnas ``Ajustados`` y ``Residuos``.
    """
    # Paso 1: extraer los valores ajustados y los residuos calculados por OLS.
    return pd.DataFrame(
        {"Ajustados": modelo.fittedvalues, "Residuos": modelo.resid}
    ).reset_index(drop=True)


def prueba_shapiro(
    residuos: Sequence[float] | pd.Series | np.ndarray,
    alfa: float = 0.05,
) -> tuple[float, float, str]:
    """Evalúa la normalidad de los residuos con Shapiro-Wilk.

    Args:
        residuos: Residuos del modelo.
        alfa: Nivel de significancia para la conclusión.

    Returns:
        Tupla con estadístico W, p-valor y conclusión en español.

    Raises:
        ValueError: Si alfa no está entre 0 y 1, o hay menos de tres residuos.
    """
    # Paso 1: validar alfa y disponer los residuos como valores numéricos.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1.")
    valores = np.asarray(residuos, dtype=float)
    if valores.size < 3:
        raise ValueError("La prueba de Shapiro-Wilk requiere al menos tres residuos.")

    # Paso 2: aplicar Shapiro-Wilk; H0 establece que los residuos son normales.
    estadistico, p_valor = shapiro(valores)
    if p_valor >= alfa:
        conclusion = (
            f"No se rechaza H₀ (p = {p_valor:.4g} ≥ α = {alfa:g}): "
            "no se detecta evidencia de falta de normalidad."
        )
    else:
        conclusion = (
            f"Se rechaza H₀ (p = {p_valor:.4g} < α = {alfa:g}): "
            "hay evidencia de que los residuos no siguen una distribución normal."
        )
    return float(estadistico), float(p_valor), conclusion


def prueba_levene(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[float, float, str]:
    """Evalúa la igualdad de varianzas por tratamiento con la prueba de Levene.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna de tratamientos.
        col_resp: Nombre de la columna de respuesta numérica.
        alfa: Nivel de significancia para la conclusión.

    Returns:
        Tupla con estadístico, p-valor y conclusión en español.

    Raises:
        ValueError: Si alfa no está entre 0 y 1 o faltan columnas requeridas.
    """
    # Paso 1: validar argumentos y construir un grupo de respuestas por tratamiento.
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1.")
    faltantes = [col for col in (col_trat, col_resp) if col not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan las columnas requeridas: {', '.join(faltantes)}.")
    if col_trat == col_resp:
        raise ValueError("La columna de tratamiento y la de respuesta deben ser distintas.")
    grupos = [
        pd.to_numeric(grupo[col_resp], errors="raise").to_numpy(dtype=float)
        for _, grupo in df.groupby(col_trat, dropna=True)
    ]
    if len(grupos) < 2:
        raise ValueError("La prueba de Levene requiere al menos dos tratamientos.")

    # Paso 2: aplicar Levene centrada en la mediana; H0 establece varianzas iguales.
    estadistico, p_valor = levene(*grupos, center="median")
    if p_valor >= alfa:
        conclusion = (
            f"No se rechaza H₀ (p = {p_valor:.4g} ≥ α = {alfa:g}): "
            "no se detecta evidencia de varianzas diferentes."
        )
    else:
        conclusion = (
            f"Se rechaza H₀ (p = {p_valor:.4g} < α = {alfa:g}): "
            "hay evidencia de diferencias entre las varianzas de los tratamientos."
        )
    return float(estadistico), float(p_valor), conclusion


def grafico_residuos_vs_ajustados(
    datos: pd.DataFrame,
) -> go.Figure:
    """Crea un gráfico de residuos en función de valores ajustados.

    Args:
        datos: DataFrame devuelto por ``residuos_y_ajustados``.

    Returns:
        Figura Plotly con puntos de residuos y línea horizontal en cero.

    Raises:
        ValueError: Si faltan las columnas requeridas.
    """
    # Paso 1: comprobar que estén disponibles ambas series del diagnóstico.
    requeridas = {"Ajustados", "Residuos"}
    if not requeridas.issubset(datos.columns):
        raise ValueError("Se requieren las columnas 'Ajustados' y 'Residuos'.")

    # Paso 2: representar residuos frente a ajustados junto a la referencia y = 0.
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=datos["Ajustados"],
            y=datos["Residuos"],
            mode="markers",
            name="Observaciones",
        )
    )
    figura.add_hline(y=0, line_dash="dash", line_color="gray")
    figura.update_layout(
        title="Residuos vs. valores ajustados",
        xaxis_title="Valores ajustados",
        yaxis_title="Residuos",
    )
    return figura


def grafico_qq(residuos: Sequence[float] | pd.Series | np.ndarray) -> go.Figure:
    """Crea un gráfico Q-Q de los residuos frente a una distribución normal.

    Args:
        residuos: Residuos del modelo.

    Returns:
        Figura Plotly con cuantiles observados y línea de referencia normal.

    Raises:
        ValueError: Si hay menos de dos residuos.
    """
    # Paso 1: calcular cuantiles teóricos, observados y recta normal de referencia.
    valores = np.asarray(residuos, dtype=float)
    if valores.size < 2:
        raise ValueError("El gráfico Q-Q requiere al menos dos residuos.")
    (cuantiles_teoricos, cuantiles_observados), (pendiente, intercepto, _) = probplot(
        valores, dist="norm", fit=True
    )
    x_linea = np.asarray([cuantiles_teoricos[0], cuantiles_teoricos[-1]])
    y_linea = intercepto + pendiente * x_linea

    # Paso 2: dibujar los cuantiles observados junto con la recta de referencia.
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=cuantiles_teoricos,
            y=cuantiles_observados,
            mode="markers",
            name="Residuos",
        )
    )
    figura.add_trace(
        go.Scatter(
            x=x_linea,
            y=y_linea,
            mode="lines",
            name="Referencia normal",
        )
    )
    figura.update_layout(
        title="Gráfico Q-Q de los residuos",
        xaxis_title="Cuantiles teóricos normales",
        yaxis_title="Cuantiles observados",
    )
    return figura
