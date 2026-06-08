"""
Preprocesamiento para embeddings.

Toma como entrada el CSV del scraping (mínimo: video_id, comment_id,
parent_id, is_reply, autor, texto, likes, fecha, fecha_descarga, estado_video).

Salida: mismos metadatos + columna 'texto_clean' lista para modelos de embeddings.
"""

import pandas as pd
import re
from langdetect import detect, LangDetectException

# === CONFIG ===

INPUT_FILE = "comentarios_multivideo_robusto2.csv"
OUTPUT_FILE = "comentarios_para_embeddings.csv"

TEXT_COL = "texto"
STATUS_COL = "estado_video"

# Filtros de calidad para el texto a embeddear
MIN_CHAR_LEN = 10
MIN_WORDS = 2

# Filtrar solo español; cambiar a False si el corpus es multilingüe
USAR_FILTRO_IDIOMA = True
IDIOMA_OBJETIVO = "es"


# === FUNCTIONS ===

def cargar_datos():
    """Lee el CSV original y devuelve un DataFrame."""
    print(f"Leyendo: {INPUT_FILE}")
    df = pd.read_csv(
        INPUT_FILE,
        sep=";",
        encoding="utf-8",
        engine="python"
    )

    if TEXT_COL not in df.columns:
        raise ValueError(f"Columna de texto '{TEXT_COL}' no encontrada. Disponibles: {list(df.columns)}")

    if STATUS_COL not in df.columns:
        raise ValueError(f"Columna de estado '{STATUS_COL}' no encontrada. Disponibles: {list(df.columns)}")

    print(f"Filas cargadas: {len(df)}")
    return df


def limpiar_texto_para_embeddings(texto):
    """
    Limpieza mínima para embeddings.
    Se eliminan URLs, marcas de tiempo y se normaliza el espacio, pero se conservan
    puntuación y emojis porque aportan información semántica al modelo.
    """
    if not isinstance(texto, str):
        texto = str(texto)

    texto = texto.strip()
    texto = texto.replace("\n", " ").replace("\r", " ")
    texto = re.sub(r"http\S+|www\.\S+", "", texto)
    texto = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\b", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    texto = texto.lower().strip()

    return texto


def detectar_idioma_seguro(texto):
    """
    Detecta el idioma con langdetect.
    Devuelve 'unknown' para textos cortos o que no se pueden procesar.
    """
    if not isinstance(texto, str):
        return "unknown"
    texto = texto.strip()
    if len(texto) < 3:
        return "unknown"
    try:
        return detect(texto)
    except (LangDetectException, Exception):
        return "unknown"


def aplicar_filtros_de_calidad(df):
    """
    Aplica filtros de calidad en secuencia:
    1. Conservar solo filas descargadas con éxito
    2. Eliminar texto NaN
    3. Limpiar texto -> 'texto_clean'
    4. Eliminar textos vacíos tras la limpieza
    5. Filtrar por longitud mínima (chars y palabras)
    6. Filtrar por idioma (opcional)
    """
    # 1. Solo descargas exitosas
    antes = len(df)
    df = df[df[STATUS_COL] == "EXITO"].copy()
    print(f"Tras filtro de estado: {len(df)} filas (descartadas {antes - len(df)})")

    # 2. Eliminar NaN
    df = df.dropna(subset=[TEXT_COL]).reset_index(drop=True)
    print(f"Tras eliminar NaN: {len(df)} filas")

    # 3. Limpiar
    print("Limpiando texto para embeddings...")
    df["texto_clean"] = df[TEXT_COL].apply(limpiar_texto_para_embeddings)

    # 4. Eliminar textos vacíos
    antes = len(df)
    df = df[df["texto_clean"].str.strip() != ""].copy()
    print(f"Tras eliminar textos vacíos: {len(df)} filas (descartadas {antes - len(df)})")

    # 5. Filtros de longitud
    df["n_chars"] = df["texto_clean"].str.len()
    df["n_words"] = df["texto_clean"].str.split().apply(len)

    antes = len(df)
    df = df[
        (df["n_chars"] >= MIN_CHAR_LEN) &
        (df["n_words"] >= MIN_WORDS)
    ].copy()
    print(f"Tras filtro de longitud: {len(df)} filas (descartadas {antes - len(df)})")

    # 6. Filtro de idioma
    if USAR_FILTRO_IDIOMA:
        print("Detectando idioma...")
        df["lang"] = df["texto_clean"].apply(detectar_idioma_seguro)
        antes = len(df)
        df = df[df["lang"] == IDIOMA_OBJETIVO].copy().reset_index(drop=True)
        print(f"Solo español: {len(df)} (descartadas {antes - len(df)})")
    else:
        df["lang"] = "unknown"

    return df


def seleccionar_columnas_salida(df):
    """
    Selecciona las columnas a conservar: metadatos de trazabilidad + texto limpio.
    Solo incluye columnas que existan en el DataFrame.
    """
    columnas_basicas = [
        "video_id",
        "comment_id",
        "parent_id",
        "is_reply",
        "autor",
        "likes",
        "fecha",
        "fecha_descarga",
        STATUS_COL,
        TEXT_COL,
        "texto_clean",
        "n_chars",
        "n_words",
        "lang",
    ]

    columnas_presentes = [c for c in columnas_basicas if c in df.columns]
    return df[columnas_presentes].copy()


def main():
    # 1. Load raw data
    df = cargar_datos()

    # 2. Filter and clean
    df = aplicar_filtros_de_calidad(df)

    # 3. Select output columns
    df_salida = seleccionar_columnas_salida(df)

    # 4. Guardar
    print(f"Guardando en: {OUTPUT_FILE}")
    df_salida.to_csv(OUTPUT_FILE, sep=";", encoding="utf-8", index=False)
    print("Listo.")


if __name__ == "__main__":
    main()
