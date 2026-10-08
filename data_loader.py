"""
data_loader.py
Carga y filtrado del dataset de ciberseguridad Argentina.
Uso: from data_loader import cargar_datos, filtrar_por_nivel
"""

import pandas as pd
from pathlib import Path

# El csv se encuentra en la carpeta raíz, junto con "data_loader.py" y "streamlit_app.py"
RUTA_CSV = Path(__file__).resolve().parent / "ciberseguridad_argentina_dataset.csv"


def cargar_datos(ruta: Path = RUTA_CSV) -> pd.DataFrame:
    """Lee el CSV y devuelve el DataFrame base sin modificar filas."""
    df = pd.read_csv(ruta)
    return df


def filtrar_por_nivel(df: pd.DataFrame, nivel: str) -> pd.DataFrame:
    """
    Devuelve solo las filas de un nivel (personal / gubernamental).
    Ordena por periodo_año para que los gráficos salgan en orden cronológico.
    """
    nivel = nivel.lower().strip()
    subset = df[df["nivel"] == nivel].copy()
    subset = subset.sort_values("periodo_año")
    return subset


def metricas_disponibles(df: pd.DataFrame, nivel: str) -> list:
    """Lista las métricas únicas de un nivel."""
    subset = filtrar_por_nivel(df, nivel)
    return sorted(subset["metrica"].unique().tolist())


if __name__ == "__main__":
    df = cargar_datos()
    for nivel in ["personal", "gubernamental"]:
        subset = filtrar_por_nivel(df, nivel)
        print(f"{nivel}: {len(subset)} filas, {subset['metrica'].nunique()} métricas distintas")